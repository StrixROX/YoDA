import signal
import threading
import time

from app_streams.events import AppEventStream, SystemEvent
from comms.server import start_comms_server
from .events import event_handler


def start(port: int):
    event_stream = AppEventStream()

    # startup event
    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_ONLINE))

    # add a SIGINT signal handler before starting persistent threads
    shutdown_signal = threading.Event()

    def shutdown_handler(sig, frame):
        event_stream.push(SystemEvent(SystemEvent.USR_REQ_SHUTDN))
        shutdown_signal.set()

    signal.signal(signal.SIGINT, shutdown_handler)

    # event handling thread
    event_handler_thread = threading.Thread(
        target=event_handler, args=(event_stream, shutdown_signal)
    )
    # comms server thread to receive CLI commands
    comms_server_thread = threading.Thread(
        target=start_comms_server, args=(port, event_stream, shutdown_signal)
    )

    event_handler_thread.start()
    comms_server_thread.start()

    # keep the main thread alive to process signals
    try:
        while not shutdown_signal.is_set():
            time.sleep(1.0)
    finally:
        event_handler_thread.join()
        comms_server_thread.join()
