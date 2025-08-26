import threading
import time
from types import MethodType


class ThreadController:
    def __init__(self) -> None:
        self.controllers = dict()
        self.shutdown_signal = threading.Event()

    def register(self, name: str, target: MethodType, args: tuple) -> None:
        if name in self.controllers.keys():
            raise ValueError(f"Controller with name '{name}' already exists.")

        self.controllers[name] = {
            "is_ok": False,
            "is_setup_complete": False,
            "thread": None,
        }

        def on_setup_complete(is_ok):
            self.controllers[name]["is_setup_complete"] = True
            self.controllers[name]["is_ok"] = is_ok

        self.controllers[name]["thread"] = threading.Thread(
            target=target,
            args=(*args, on_setup_complete, self.shutdown_signal),
        )

    def start_all(self, callback: MethodType) -> None:
        for key in self.controllers:
            thread = self.controllers[key]["thread"]
            thread.start()

        def await_setup():
            while not all(self.get_setup_status().values()):
                time.sleep(0.5)

            callback()

        threading.Thread(target=await_setup).start()

    def stop_all(self) -> None:
        self.shutdown_signal.set()

    def join_all(self) -> None:
        for key in self.controllers:
            thread = self.controllers[key]["thread"]
            thread.join()

    def get_setup_status(self):
        statuses = {}

        for name in self.controllers:
            statuses[name] = self.controllers[name]["is_setup_complete"]

        return statuses

    def get_status(self):
        statuses = {}

        for name in self.controllers:
            statuses[name] = self.controllers[name]["is_ok"]

        return statuses
