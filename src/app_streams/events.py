import queue


class AppEvent:
    def __init__(self, type: str, message: str) -> None:
        if not message:
            raise ValueError("No message provided for AppEvent.")

        if len(message.strip()) == 0:
            raise ValueError("Event message is empty.")

        self.type = type
        self.message = message

    def __str__(self) -> str:
        return f"<AppEvent type=('{self.type}') message=('{self.message}')>"


class SystemEvent(AppEvent):
    def __init__(self, message: str) -> None:
        super().__init__("system-event", message)


class UserMessageEvent(AppEvent):
    def __init__(self, message: str) -> None:
        super().__init__("user", message)


class AppEventStream(queue.Queue):
    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize)

    def push(self, event) -> None:
        if not isinstance(event, AppEvent):
            raise ValueError(
                f"Only AppEvent instances can be pushed to AppEventStream, received: {type(event)}"
            )

        self.put_nowait(event)
