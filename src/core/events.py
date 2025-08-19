import threading
from typing import Union
from app_streams.events import AppEventStream, SystemEvent
from llm.tts import system_speak


def event_handler(event_stream: AppEventStream, shutdown_signal: threading.Event) -> None:
    while True:
        event = event_stream.get()
        print(event)

        if isinstance(event, SystemEvent):
            threading.Thread(
                target=system_event_handler, args=(event, event_stream)
            ).start()
        
        # stop event processing on shutdown signal
        if shutdown_signal.is_set():
            break


def system_event_handler(event: SystemEvent, event_stream: AppEventStream) -> None:
    if event.message == SystemEvent.CORE_SYS_ONLINE:
        startup_greeting = "Core system online. Welcome!"

        def on_complete_callback(success: bool, error: Union[Exception, None]):
            if success:
                event_stream.push(
                    SystemEvent(SystemEvent.SYS_SPEAK_OK, startup_greeting)
                )
            else:
                event_stream.push(
                    SystemEvent(
                        SystemEvent.SYS_SPEAK_ERR,
                        {"text_content": startup_greeting, "error": error},
                    )
                )

        system_speak(startup_greeting, on_complete_callback)
