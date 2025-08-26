import signal
import time

from app_streams.events import AppEventStream, SystemEvent
from comms.server import start_comms_server
from core.controller import ThreadController
from .events import event_handler


def start(port: int):
    event_stream = AppEventStream()

    controller = ThreadController()
    controller.register("event-handler", event_handler, (event_stream,))
    controller.register("comms-server", start_comms_server, (port, event_stream))

    # startup event
    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_START, controller.get_status()))

    # add a SIGINT signal handler before starting persistent threads
    def shutdown_handler(sig, frame):
        event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))
        controller.stop_all()

    signal.signal(signal.SIGINT, shutdown_handler)

    # start the threads
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
