from concurrent.futures import ThreadPoolExecutor
import ssl
import threading

from app_streams.events import (
    AppEventStream,
    SystemEvent,
    UserMessageEvent,
)
from comms.client import listen_for_messages
from comms.server import get_is_socket_connected, listen_for_connections, start_server


class CommsServer:
    def __init__(
        self,
        port: int,
        event_stream: AppEventStream,
        thread_pool_executor: ThreadPoolExecutor,
        shutdown_signal: threading.Event,
    ) -> None:
        self.hostname = "localhost"
        self.port = port

        self.ssock = None
        self.is_done = threading.Event()
        self.is_ready = threading.Event()

        self.__shutdown_signal = shutdown_signal
        self.__event_stream = event_stream
        self.__thread_pool_executor = thread_pool_executor

        self.__lock = threading.Lock()
        self.__connections = {}

        self.__thread_pool_executor.submit(self.__start)

    def __start(self) -> None:
        self.__event_stream.push(
            SystemEvent(SystemEvent.COMMS_START, (self.hostname, self.port))
        )

        start_server(
            hostname=self.hostname,
            port=self.port,
            on_start=self.__on_start,
            on_error=self.__on_error,
            on_done=self.__on_done,
        )

    def __on_done(self) -> None:
        self.is_done.set()

    def __on_start(self, ssock: ssl.SSLSocket) -> None:
        self.ssock = ssock
        self.is_ready.set()
        self.__event_stream.push(
            SystemEvent(SystemEvent.COMMS_ONLINE, (self.hostname, self.port))
        )
        self.__listen_for_connections()

    def __on_error(self, err: Exception) -> None:
        self.__event_stream.push(SystemEvent(SystemEvent.COMMS_OFFLINE, err))

    def __listen_for_connections(self) -> None:
        try:
            listen_for_connections(
                ssock=self.ssock,
                shutdown_signal=self.__shutdown_signal,
                on_client_connected=self.__on_client_connected,
            )
        except ConnectionAbortedError:
            self.__event_stream.push(SystemEvent(SystemEvent.USR_DISCONN_ABT))
        except BlockingIOError:
            pass

    def __on_client_connected(
        self, client: ssl.SSLSocket, addr: tuple[str, int]
    ) -> None:
        connection_id = hash(client)

        with self.__lock:
            self.__connections[connection_id] = client

        self.__event_stream.push(SystemEvent(SystemEvent.USR_CONN_OK, connection_id))

        def on_client_connected():
            socket_buffer = ""

            while not self.__shutdown_signal.is_set():
                print(socket_buffer)
                message, socket_buffer = listen_for_messages(client, socket_buffer)
                self.__event_stream.push(UserMessageEvent(message, connection_id))

        self.__thread_pool_executor.submit(on_client_connected)

    def get_connection_by_id(self, connection_id: int) -> ssl.SSLSocket | None:
        with self.__lock:
            if connection_id in self.__connections and get_is_socket_connected(
                self.__connections[connection_id]
            ):
                return self.__connections[connection_id]
            elif connection_id in self.__connections:
                del self.__connections[connection_id]
                return None
            else:
                return None

    def close(self) -> None:
        self.ssock.close()
