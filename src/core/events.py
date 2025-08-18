from app_streams import AppEventStream


def event_handler(event_stream: AppEventStream):
    while True:
        event = event_stream.get()
        print(event)
