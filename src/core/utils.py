import threading
import time


def poll_and_wait_for(events: list[threading.Event]):
    is_any_pending = True

    while is_any_pending:
        is_any_pending = any([not event.is_set() for event in events])
        time.sleep(0.5)
