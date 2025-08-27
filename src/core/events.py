from app_streams.events import (
    AppEvent,
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from windows_toasts import WindowsToaster, Toast


def event_handler(event: AppEvent, event_stream: AppEventStream) -> None:
    if isinstance(event, SystemEvent):
        return system_event_handler(event, event_stream)
    elif isinstance(event, SystemMessageEvent):
        return system_message_handler(event, event_stream)
    elif isinstance(event, UserMessageEvent):
        return user_message_handler(event, event_stream)


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
