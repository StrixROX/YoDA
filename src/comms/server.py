import socket
import ssl
import threading
from types import MethodType

from app_streams.events import AppEventStream, SystemEvent, UserMessageEvent

BUFFER_SIZE = 1024

CERT_FILE = "server.crt"
KEY_FILE = "server.key"


def start_comms_server(
    port: int,
    event_stream: AppEventStream,
    on_setup: MethodType,
    shutdown_signal: threading.Event,
) -> None:
    hostname = "localhost"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # now attempting to start comms server
    event_stream.push(SystemEvent(SystemEvent.COMMS_START, (hostname, port)))

    try:
        sock.bind((hostname, port))
        sock.listen()

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

        with context.wrap_socket(sock, server_side=True) as ssock:
            # if we reach this point, server must be up and running now
            event_stream.push(SystemEvent(SystemEvent.COMMS_ONLINE, (hostname, port)))
            on_setup(True)

            ssock.setblocking(False)

            while not shutdown_signal.is_set():
                try:
                    conn, addr = ssock.accept()

                    threading.Thread(
                        target=handle_client,
                        args=(conn, addr, event_stream, shutdown_signal),
                    ).start()

                except ConnectionAbortedError:
                    event_stream.push(SystemEvent(SystemEvent.USR_DISCONN_ABT))
                except BlockingIOError:
                    pass

            ssock.close()
    except Exception as err:
        # if anything breaks while starting the server, we will end up here
        event_stream.push(SystemEvent(SystemEvent.COMMS_OFFLINE, err))
        on_setup(False)


def handle_client(
    conn: ssl.SSLSocket,
    addr: tuple[str, int],
    event_stream: AppEventStream,
    shutdown_signal: threading.Event,
) -> None:
    connection_id = hash(conn)

    event_stream.push(SystemEvent(SystemEvent.USR_CONN_OK, connection_id))

    conn.setblocking(False)

    with conn:
        buffer = ""

        while not shutdown_signal.is_set():
            chunk = ""
            try:
                chunk = conn.recv(BUFFER_SIZE).decode()
                chunk = None if chunk == "" else chunk
            except ssl.SSLWantReadError:
                pass

            if chunk is None:
                break

            buffer += chunk

            dataBlock = None
            if "\0" in buffer:
                dataBlock, buffer = buffer.split("\0", 1)

            if dataBlock:
                event = UserMessageEvent(dataBlock, connection_id)
                event_stream.push(event)

    event_stream.push(SystemEvent(SystemEvent.USR_DISCONN_OK, connection_id))
