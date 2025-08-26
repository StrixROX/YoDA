from datetime import datetime as dt
import queue


class AppEvent:
    def __init__(self, type: str, message: str, data: any = None) -> None:
        if not message:
            raise ValueError("No message provided for AppEvent.")

        if len(message.strip()) == 0:
            raise ValueError("Event message is empty.")

        self.type = type
        self.message = message
        self.data = data
        self.timestamp = dt.now().timestamp()

    def __str__(self) -> str:
        return f"<AppEvent type=('{self.type}') message=('{self.message}') data=({repr(self.data)})>"


class SystemEvent(AppEvent):
    CORE_SYS_START = "Starting core systems..."  # data: { [system_name]: bool }
    CORE_SYS_FINISH = "Finished starting core systems."  # data: { [system_name]: bool }
    USR_REQ_SHUTDN = "System shutdown requested by user."  # data: None

    COMMS_START = "Starting comms server..."  # data: string
    COMMS_ONLINE = "Comms server online."  # data: string
    COMMS_OFFLINE = "Unable to start comms server."  # data: Exception

    USR_CONN_OK = "User connected to comms system."  # data: int
    USR_DISCONN_OK = "User disconnected from comms system."  # data: int
    USR_DISCONN_ABT = (
        "User disconnected from comms system. Connection aborted."  # data: None
    )

    EVENT_HANDLER_START = "Starting event handler thread..."  # data: None
    EVENT_HANDLER_ONLINE = "Event handler thread online."  # data: None
    EVENT_HANDLER_OFFLINE = "Unable to start event handler thread."  # data: Exception

    SYS_SPEAK_OK = "System completed speaking."  # data: str
    SYS_SPEAK_ERR = (
        "System unable to speak."  # data: {"text_content": str, "error": Exception}
    )

    def __init__(self, message: str, data: any = None) -> None:
        super().__init__("system-event", message, data)


class UserMessageEvent(AppEvent):
    def __init__(self, message: str, data: any = None) -> None:
        super().__init__("user", message, data)


class SystemMessageEvent(AppEvent):
    def __init__(self, message: str, data: any = None) -> None:
        super().__init__("system", message, data)


class AppEventStream(queue.Queue):
    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize)

    def push(self, event) -> None:
        if not isinstance(event, AppEvent):
            raise ValueError(
                f"Only AppEvent instances can be pushed to AppEventStream, received: {type(event)}"
            )

        self.put_nowait(event)
