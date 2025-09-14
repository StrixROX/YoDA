from collections import deque
from collections.abc import Callable
from datetime import datetime as dt
import os
from typing import Dict
from concurrent.futures import ThreadPoolExecutor


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
        return f"<AppEvent created_on=({dt.fromtimestamp(self.timestamp).isoformat()}) type=('{self.type}') message=('{self.message}') data=({repr(self.data)})>"


class SystemEvent(AppEvent):
    type = "system-event"

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

    SYS_SPEAK_OK = "System completed speaking."  # data: str
    SYS_SPEAK_ERR = (
        "System unable to speak."  # data: {"text_content": str, "error": Exception}
    )

    LLM_START = "Starting LLM server..."  # data: string
    LLM_ONLINE = "LLM server online."  # data: string
    LLM_OFFLINE = "Unable to start LLM server."  # data: Exception
    
    AGENT_ONLINE = "Agent online." # data: string
    AGENT_OFFLINE = "Agent offline." # data: Exception

    def __init__(self, message: str, data: any = None) -> None:
        super().__init__(self.type, message, data)


class UserMessageEvent(AppEvent):
    type = "user-message"

    def __init__(self, message: str, data: any = None) -> None:
        super().__init__(self.type, message, data)


class SystemMessageEvent(AppEvent):
    type = "system-message"

    def __init__(self, message: str, data: any = None) -> None:
        super().__init__(self.type, message, data)


class AppEventStream:
    DEFAULT_DUMP_FILENAME = "temp/AppEventStream_history.log"

    def __init__(self, max_workers=5, history_maxsize=None) -> None:
        self.__event_hooks: Dict[str, Dict[int, Callable[[AppEvent], None]]] = dict(
            {"all": dict()}
        )
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.history = deque(maxlen=history_maxsize)

    # If you truly know that:
    #
    # add_event_hook / remove_event_hook and push are only ever
    # called from a single thread (or at least not concurrently),
    # and
    #
    # The only concurrency in your system is from the threads
    # that the executor itself runs after a push call is complete,
    #
    # ...then you don’t need a Lock around the dict. Python dicts
    # are safe for concurrent reads, but not for concurrent
    # reads+mutations. So the moment you ever think about
    # adding/removing hooks from one thread while another is
    # pushing, you need a lock. But if your design contract is
    # "hook set mutations happen synchronously on the main thread
    # only," then it’s fine as-is.

    def __iter_hooks_for_event(self, event_type: str):
        yield from self.__event_hooks.get(event_type, {}).values()
        yield from self.__event_hooks.get("all", {}).values()

    def push(self, event) -> None:
        if not isinstance(event, AppEvent):
            raise ValueError(
                f"Only AppEvent instances can be pushed to AppEventStream, received: {type(event)}"
            )

        # send the event to all hooks registered for that event type
        # also send the event to all the hooks registered for 'all' events
        for event_hook in self.__iter_hooks_for_event(event.type):
            self.__executor.submit(event_hook, event)

        self.history.append(event)

    def add_event_hook(
        self, event_type: str, event_hook: Callable[[AppEvent], None]
    ) -> int:
        event_hook_id = hash(event_hook)

        event_hooks_for_type = self.__event_hooks.setdefault(event_type, dict())

        if event_hook_id in event_hooks_for_type:
            raise ValueError(
                f"Event hook with id {event_hook_id} already exists for event type '{event_type}'."
            )

        event_hooks_for_type[event_hook_id] = event_hook

        return event_hook_id

    def remove_event_hook(self, event_type: str, event_hook_id: int) -> None:
        event_hooks_for_type = self.__event_hooks.setdefault(event_type, dict())

        if event_hook_id not in event_hooks_for_type:
            raise ValueError(
                f"Event hook with id {event_hook_id} does not exist for event type '{event_type}'."
            )

        del event_hooks_for_type[event_hook_id]

    def close(self):
        self.__executor.shutdown()

    def dump(self, dump_filename=DEFAULT_DUMP_FILENAME):
        os.makedirs(os.path.dirname(dump_filename), exist_ok=True)
        with open(dump_filename, "w") as f:
            f.writelines([str(event) + "\n" for event in self.history])
