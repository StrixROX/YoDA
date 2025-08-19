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

    def __str__(self) -> str:
        return f"<AppEvent type=('{self.type}') message=('{self.message}') data=({repr(self.data)})>"


class SystemEvent(AppEvent):
    USR_CONN_OK = "User connected to core system."  # data: int
    USR_DISCONN_OK = "User disconnected from core system."  # data: int
    USR_DISCONN_ABT = (
        "User disconnected from core system. Connection aborted."  # data: None
    )

    CORE_SYS_ONLINE = "Core system online."  # data: None
    USR_REQ_SHUTDN = "System shutdown requested by user."  # data: None

    SYS_SPEAK_OK = "System completed speaking."  # data: str
    SYS_SPEAK_ERR = (
        "System unable to speak."  # data: {"text_content": str, "error": Exception}
    )

    def __init__(self, message: str, data: any = None) -> None:
        super().__init__("system-event", message, data)


class UserMessageEvent(AppEvent):
    def __init__(self, message: str, data: any = None) -> None:
        super().__init__("user", message, data)


class AppEventStream(queue.Queue):
    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize)

    def push(self, event) -> None:
        if not isinstance(event, AppEvent):
            raise ValueError(
                f"Only AppEvent instances can be pushed to AppEventStream, received: {type(event)}"
            )

        self.put_nowait(event)
