from concurrent.futures import ThreadPoolExecutor
import subprocess
import threading
from app_streams.events import LLM_OFFLINE, LLM_ONLINE, LLM_START, AppEvent, SystemEvent
from llm.server import get_is_ollama_server_running, start_ollama_server


class OllamaServer:
    def __init__(
        self,
        port: int,
        event_stream: AppEvent,
        thread_pool_executor: ThreadPoolExecutor,
        shutdown_signal: threading.Event,
    ) -> None:
        self.hostname = "localhost"
        self.port = port

        self.process = None
        self.is_done = threading.Event()
        self.is_ready = threading.Event()

        self.__shutdown_signal = shutdown_signal
        self.__event_stream = event_stream
        self.__thread_pool_executor = thread_pool_executor

        self.__thread_pool_executor.submit(self.__start)

    def get_server_url(self):
        return f"http://{self.hostname}:{self.port}"

    def __start(self) -> None:
        ollama_server_url = self.get_server_url()

        self.__event_stream.push(SystemEvent(LLM_START, ollama_server_url))

        is_server_already_running = get_is_ollama_server_running(
            base_url=ollama_server_url
        )

        if is_server_already_running:
            self.__on_done()
            self.__on_start(process=None)
        else:
            start_ollama_server(
                on_start=self.__on_start,
                on_error=self.__on_error,
                on_done=self.__on_done,
            )

    def __on_done(self) -> None:
        self.is_done.set()

    def __on_start(self, process: subprocess.Popen) -> None:
        self.process = process

        self.__event_stream.push(SystemEvent(LLM_ONLINE, self.get_server_url()))
        self.is_ready.set()

        if self.process is not None:
            # now wait for shutdown signal
            self.__shutdown_signal.wait()
            self.close()

    def __on_error(self, err: Exception) -> None:
        self.__event_stream.push(SystemEvent(LLM_OFFLINE, err))

    def close(self) -> None:
        if (
            self.is_ready.is_set()
            and self.process is not None
            and self.process.poll() is None
        ):
            self.process.terminate()
            try:
                # wait up to 5 seconds for graceful shutdown
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()  # force kill if it doesn't terminate gracefully
