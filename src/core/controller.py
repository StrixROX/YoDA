import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import MethodType


class ThreadedServiceSetupController:
    """
    Lets you register a bunch of functions as Threads and gives you option to
    control them all simultaneously. It also keeps track of which
    functions have been setup successfully.
    """

    def __init__(self, max_workers=None) -> None:
        self.controllers = dict()
        self.shutdown_signal = threading.Event()
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.__futures = {}

    def register(self, name: str, target: MethodType, args: tuple) -> None:
        if name in self.controllers.keys():
            raise ValueError(f"Controller with name '{name}' already exists.")

        self.controllers[name] = {
            "is_ok": False,
            "is_setup_complete": False,
            "target": target,
            "args": args,
        }

        def on_setup_complete(is_ok):
            self.controllers[name]["is_setup_complete"] = True
            self.controllers[name]["is_ok"] = is_ok

        self.controllers[name]["on_setup_complete"] = on_setup_complete

    def start_all(self, callback: MethodType) -> None:
        # Submit all tasks to the executor
        for name, controller in self.controllers.items():
            target = controller["target"]
            args = controller["args"]
            on_setup_complete = controller["on_setup_complete"]

            future = self.__executor.submit(
                target, *args, on_setup_complete, self.shutdown_signal
            )
            self.__futures[name] = future

        def await_setup():
            while not all(self.get_setup_status().values()):
                time.sleep(0.5)

            callback()

        # Use executor for the await_setup thread as well
        self.__executor.submit(await_setup)

    def stop_all(self) -> None:
        self.shutdown_signal.set()
        # Shutdown the executor gracefully
        self.__executor.shutdown(wait=False)

    def join_all(self) -> None:
        # Wait for all futures to complete
        for future in self.__futures.values():
            try:
                future.result()  # This will wait for completion and raise any exceptions
            except Exception as e:
                # Log or handle exceptions as needed
                print(f"Task failed with exception: {e}")

        # Ensure executor is properly shutdown
        if not self.__executor._shutdown:
            self.__executor.shutdown(wait=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_all()
        self.join_all()

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
