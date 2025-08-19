import threading
from comms import start_comms_server
from app_streams import AppEventStream, SystemEvent
from .events import event_handler


def main(port: int):
    event_stream = AppEventStream()

    # startup event
    event_stream.push(SystemEvent(SystemEvent.CORE_SYS_ONLINE))

    # event handling thread
    threading.Thread(target=event_handler, args=(event_stream,)).start()

    # comms server thread to receive CLI commands
    threading.Thread(target=start_comms_server, args=(port, event_stream)).start()
