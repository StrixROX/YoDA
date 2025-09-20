import argparse
from concurrent.futures import ThreadPoolExecutor
import signal
import threading
import time


from app_streams.events import (
    AppEventStream,
    SystemEvent,
    UserMessageEvent,
)
from core.events_handlers import (
    on_core_system_ready,
    on_user_message,
)

from core.services import CommsServer
from core.services.llm_server import OllamaServer
from core.utils import poll_and_wait_for

from llm.agent import Agent


def start_core_system(args: argparse.Namespace) -> None:
    """
    There are two parts to the core system: event_hooks and services.

    event_hooks -> no startup logs. if these fail, the whole program exits.
    services -> startup logs are generated. if these fail, the program keeps running normally.
    """

    # add a SIGINT signal handler before starting persistent threads
    shutdown_signal = threading.Event()

    def shutdown_handler(sig, frame):
        shutdown_signal.set()
        event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))

    signal.signal(signal.SIGINT, shutdown_handler)

    thread_pool_executor = ThreadPoolExecutor(max_workers=16)
    event_stream = AppEventStream(thread_pool_executor)

    setup_early_hooks(event_stream)

    comms_server, llm_server, agent = setup_services(
        args, event_stream, shutdown_signal, thread_pool_executor
    )

    setup_event_hooks(
        event_stream=event_stream,
        comms_server=comms_server,
        llm_server=llm_server,
        agent=agent,
    )

    # keep the main thread alive to process signals
    while not shutdown_signal.is_set():
        time.sleep(1.0)
    else:
        comms_server.close()
        llm_server.close()
        event_stream.close()
        event_stream.dump()


def setup_services(
    args: argparse.Namespace,
    event_stream: AppEventStream,
    shutdown_signal: threading.Event,
    thread_pool_executor: ThreadPoolExecutor,
) -> tuple[CommsServer, OllamaServer, Agent]:
    """Start all the related services"""

    status = {
        "comms-server": False,
        "llm-server": False,
        "agent": False,
    }

    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_START, status))

    comms_server = CommsServer(
        port=args.port_comms,
        event_stream=event_stream,
        shutdown_signal=shutdown_signal,
        thread_pool_executor=thread_pool_executor,
    )

    llm_server = OllamaServer(
        port=args.port_ollama,
        event_stream=event_stream,
        shutdown_signal=shutdown_signal,
        thread_pool_executor=thread_pool_executor,
    )

    poll_and_wait_for([comms_server.is_done, llm_server.is_done])

    agent = Agent(
        llm_server=llm_server,
        event_stream=event_stream,
        shutdown_signal=shutdown_signal,
    )

    status["comms-server"] = comms_server.is_ready.is_set()
    status["llm-server"] = llm_server.is_ready.is_set()
    status["agent"] = agent.is_ready.is_set()

    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_FINISH, status))

    return comms_server, llm_server, agent


def setup_early_hooks(event_stream: AppEventStream):
    event_stream.add_event_hook(
        event_type=SystemEvent.type,
        event_hook=lambda event: on_core_system_ready(event, event_stream),
    )


def setup_event_hooks(
    event_stream: AppEventStream,
    comms_server: CommsServer,
    llm_server: OllamaServer,
    agent: Agent,
) -> None:
    """Setup event hooks for the event stream."""

    event_stream.add_event_hook(
        event_type=UserMessageEvent.type,
        event_hook=lambda event: on_user_message(
            event, event_stream, comms_server, agent
        ),
    )
