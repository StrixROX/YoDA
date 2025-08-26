import threading
from types import MethodType
from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from windows_toasts import WindowsToaster, Toast


def event_handler(
    event_stream: AppEventStream,
    on_setup: MethodType,
    shutdown_signal: threading.Event,
) -> None:
    event_stream.push(SystemEvent(SystemEvent.EVENT_HANDLER_START))
    is_handler_status_pushed = False

    while True:
        event = None
        try:
            event = event_stream.get()
            if not is_handler_status_pushed:
                event_stream.push(SystemEvent(SystemEvent.EVENT_HANDLER_ONLINE))
                is_handler_status_pushed = True
                on_setup(True)
        except Exception as err:
            event_stream.push(SystemEvent(SystemEvent.EVENT_HANDLER_OFFLINE, err))
            is_handler_status_pushed = True
            on_setup(False)
            break

        print(f"[{event.type}] {event.message}", event.data)

        if isinstance(event, SystemEvent):
            threading.Thread(
                target=system_event_handler, args=(event, event_stream)
            ).start()
        elif isinstance(event, SystemMessageEvent):
            threading.Thread(
                target=system_message_handler, args=(event, event_stream)
            ).start()
        elif isinstance(event, UserMessageEvent):
            threading.Thread(
                target=user_message_handler, args=(event, event_stream)
            ).start()

        # stop event processing on shutdown signal
        if shutdown_signal.is_set():
            break


# LLM calls on system events will go here
def system_event_handler(
    event: SystemEvent,
    event_stream: AppEventStream,
) -> None:
    if event.message == SystemEvent.CORE_SYS_FINISH:
        core_systems_status = event.data

        startup_greeting = (
            "Welcome! All core systems online!"
            if all(core_systems_status.values())
            else "Welcome! Some core systems are offline."
        )

        event_stream.push(SystemMessageEvent(startup_greeting))


# TTS/GUI Render calls will go here
def system_message_handler(
    event: SystemMessageEvent,
    event_stream: AppEventStream,
) -> None:
    toaster = WindowsToaster("YoDA")
    newToast = Toast()
    newToast.text_fields = [event.message]
    toaster.show_toast(newToast)


# LLM calls on user input will go here
def user_message_handler(
    event: UserMessageEvent,
    event_stream: AppEventStream,
) -> None:
    event_stream.push(SystemMessageEvent(f"Responding to: {event.message}"))
