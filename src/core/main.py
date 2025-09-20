import argparse
from concurrent.futures import ThreadPoolExecutor
import signal
import threading
import time

from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from comms.utils import pack_msg
from core.controller import ThreadedServiceSetupController
from core.events_handlers import (
    system_event_handler,
    system_message_handler,
    user_message_handler,
)

from core.services import CommsServer
from llm.agent import Agent
from llm.server import start_llm_server


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
    controller: ThreadedServiceSetupController,
    event_stream: AppEventStream,
    comms_port: int,
    ollama_port: int,
) -> None:
    """Register services with the controller."""
    # controller.register("comms-server", start_comms_server, (comms_port, event_stream, handle_client))

    controller.register("llm-server", start_llm_server, (ollama_port, event_stream))


def start_core_system(args: argparse.Namespace) -> None:
    """
    There are two parts to the core system: event_hooks and services.

    event_hooks -> no startup logs. if these fail, the whole program exits.
    services -> startup logs are generated. if these fail, the program keeps running normally.
    """

    comms_port = args.port_comms
    ollama_port = args.port_ollama

    # add a SIGINT signal handler before starting persistent threads
    shutdown_signal = threading.Event()

    def shutdown_handler(sig, frame):
        shutdown_signal.set()
        event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))

    signal.signal(signal.SIGINT, shutdown_handler)

    thread_pool_executor = ThreadPoolExecutor(max_workers=16)
    event_stream = AppEventStream(thread_pool_executor)

    service_statuses = {"comms-server": False}

    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_START, {**service_statuses}))

    comms = CommsServer(
        port=comms_port,
        event_stream=event_stream,
        shutdown_signal=shutdown_signal,
        thread_pool_executor=thread_pool_executor,
    )

    comms.is_done.wait()

    service_statuses["comms-server"] = comms.is_ready.is_set()

    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_FINISH, {**service_statuses}))

    def on_user_message(event: UserMessageEvent):
        print(event)
        comms.get_connection_by_id(event.data).sendall(
            pack_msg("responding to: " + event.message)
        )

    event_stream.add_event_hook(UserMessageEvent.type, on_user_message)

    # controller = ThreadedServiceSetupController()
    # agent = Agent(
    #     ollama_url=f"http://localhost:{ollama_port}", event_stream=event_stream
    # )

    # # setup event hooks
    # setup_event_hooks(event_stream, agent)

    # # # setup services
    # # setup_services(controller, event_stream, comms_port, ollama_port)

    # # add a SIGINT signal handler before starting persistent threads
    # def shutdown_handler(sig, frame):
    #     event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))
    #     controller.stop_all()

    # signal.signal(signal.SIGINT, shutdown_handler)

    # comms_service = CommsServerService(event_stream=event_stream, port=comms_port, shutdown_signal=)
    # threading.Thread( target=comms_service.start).start()

    # # push startup event
    # event_stream.push(SystemEvent(SystemEvent.CORE_SYS_START, controller.get_status()))

    # # start the services
    # controller.start_all(
    #     lambda: event_stream.push(
    #         SystemEvent(SystemEvent.CORE_SYS_FINISH, controller.get_status())
    #     )
    # )

    # keep the main thread alive to process signals
    try:
        while not shutdown_signal.is_set():
            time.sleep(1.0)
    finally:
        # controller.join_all()
        comms.close()
        event_stream.close()
        event_stream.dump()
