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
from llm.server import start_llm_server


def setup_event_hooks(event_stream: AppEventStream) -> None:
    """Setup event hooks for the event stream."""
    event_stream.add_event_hook(
        event_type=SystemEvent.type,
        event_hook=system_event_handler,
    )
    event_stream.add_event_hook(
        event_type=SystemMessageEvent.type,
        event_hook=system_message_handler,
    )
    event_stream.add_event_hook(
        event_type=UserMessageEvent.type,
        event_hook=user_message_handler,
    )


def setup_services(
    controller: ThreadedServiceSetupController, event_stream: AppEventStream, port: int
) -> None:
    """Register services with the controller."""
    controller.register("comms-server", start_comms_server, (port, event_stream))
    controller.register("llm-server", start_llm_server, (event_stream,))


def start(port: int) -> None:
    """
    There are two parts to the core system: event_hooks and services.

    event_hooks -> no startup logs. if these fail, the whole program exits.
    services -> startup logs are generated. if these fail, the program keeps running normally.
    """

    event_stream = AppEventStream(max_workers=5)
    controller = ThreadedServiceSetupController()

    # setup event hooks
    setup_event_hooks(event_stream)

    # setup services
    setup_services(controller, event_stream, port)

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
