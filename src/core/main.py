import argparse
from concurrent.futures import ThreadPoolExecutor
import signal
import threading
import time

from langchain_core.messages import ChatMessage

from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from comms.utils import pack_msg
from core.events_handlers import (
    system_event_handler,
    system_message_handler,
    user_message_handler,
)

from core.services import CommsServer
from core.services.llm_server import OllamaServer
from core.utils import poll_and_wait_for

from llm.agent import Agent


def setup_event_hooks(event_stream: AppEventStream, agent: Agent) -> None:
    """Setup event hooks for the event stream."""
    event_stream.add_event_hook(
        event_type=SystemEvent.type,
        event_hook=lambda event: system_event_handler(event, event_stream, agent),
    )
    event_stream.add_event_hook(
        event_type=SystemMessageEvent.type,
        event_hook=lambda event: system_message_handler(event, event_stream),
    )
    event_stream.add_event_hook(
        event_type=UserMessageEvent.type,
        event_hook=lambda event: user_message_handler(event, event_stream, agent),
    )


def setup_services(
    args: argparse.Namespace,
    event_stream: AppEventStream,
    shutdown_signal: threading.Event,
    thread_pool_executor: ThreadPoolExecutor,
) -> tuple[CommsServer, OllamaServer]:
    """Start all the related services"""

    status = {
        "comms-server": False,
        "llm-server": False,
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

    status["comms-server"] = comms_server.is_ready.is_set()
    status["llm-server"] = llm_server.is_ready.is_set()

    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_FINISH, status))

    return comms_server, llm_server


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

    # event_stream.add_event_hook("all", print)

    comms_server, llm_server = setup_services(
        args, event_stream, shutdown_signal, thread_pool_executor
    )

    agent = Agent(
        ollama_url=llm_server.get_server_url(),
        event_stream=event_stream,
        shutdown_signal=shutdown_signal,
    )

    def on_user_message(event: UserMessageEvent):
        try:
            response = agent.invoke(
                ChatMessage(role=UserMessageEvent.type, content=event.message)
            )

            comms_server.get_connection_by_id(event.data).send(pack_msg(response))
            # comms_server.get_connection_by_id(event.data).sendall(
            #     pack_msg("responding to: " + event.message)
            # )
        except Exception as e:
            print(e)

    event_stream.add_event_hook(UserMessageEvent.type, on_user_message)

    # keep the main thread alive to process signals
    while not shutdown_signal.is_set():
        time.sleep(1.0)
    else:
        comms_server.close()
        llm_server.close()
        event_stream.close()
        event_stream.dump()
