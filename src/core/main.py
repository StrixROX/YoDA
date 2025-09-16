import argparse
import signal
import time

from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from comms.server import start_comms_server
from core.controller import ThreadedServiceSetupController
from core.events_handlers import (
    system_event_handler,
    system_message_handler,
    user_message_handler,
)
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
    controller.register("comms-server", start_comms_server, (comms_port, event_stream))
    controller.register("llm-server", start_llm_server, (ollama_port, event_stream))


def start(args: argparse.Namespace) -> None:
    """
    There are two parts to the core system: event_hooks and services.

    event_hooks -> no startup logs. if these fail, the whole program exits.
    services -> startup logs are generated. if these fail, the program keeps running normally.
    """

    comms_port = args.port_comms
    ollama_port = args.port_ollama

    event_stream = AppEventStream(max_workers=5)
    controller = ThreadedServiceSetupController()
    agent = Agent(
        ollama_url=f"http://localhost:{ollama_port}", event_stream=event_stream
    )

    # setup event hooks
    setup_event_hooks(event_stream, agent)

    # setup services
    setup_services(controller, event_stream, comms_port, ollama_port)

    # add a SIGINT signal handler before starting persistent threads
    def shutdown_handler(sig, frame):
        event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))
        controller.stop_all()

    signal.signal(signal.SIGINT, shutdown_handler)

    # push startup event
    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_START, controller.get_status()))

    # start the services
    controller.start_all(
        lambda: event_stream.push(
            SystemEvent(SystemEvent.CORE_SYS_FINISH, controller.get_status())
        )
    )

    # keep the main thread alive to process signals
    try:
        while not controller.shutdown_signal.is_set():
            time.sleep(1.0)
    finally:
        controller.join_all()
        event_stream.close()
        event_stream.dump()
