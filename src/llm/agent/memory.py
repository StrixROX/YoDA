import threading

from langchain_core.messages import BaseMessage


class AgentSessionMemory:
    def __init__(self, init_history: list[BaseMessage] = []) -> None:
        self.lock = threading.Lock()
        self._history: list[BaseMessage] = init_history

    def get(self):
        return [*self._history]

    def update(self, messages: list[BaseMessage]) -> None:
        # print("-> about to update history")
        with self.lock:
            # print("-> acquired lock")
            self._history += messages
            # print("-> history updated. releasing lock...")
        # print("-> lock released")
