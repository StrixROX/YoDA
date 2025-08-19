from app_streams import AppEventStream


def event_handler(event_stream: AppEventStream) -> None:
    while True:
        event = event_stream.get()
        print(event)
