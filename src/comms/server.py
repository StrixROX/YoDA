import socket
import ssl
import threading

from app_streams.events import AppEventStream, SystemEvent, UserMessageEvent

SOCKET_CONN_TIMEOUT = 1.0 # seconds
BUFFER_SIZE = 1024

CERT_FILE = "server.crt"
KEY_FILE = "server.key"


def start_comms_server(
    port: int, event_stream: AppEventStream, shutdown_signal: threading.Event
) -> None:
    hostname = "localhost"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.bind((hostname, port))
    sock.listen()
    print(f"Socket listening at {hostname}:{port}...")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    with context.wrap_socket(sock, server_side=True) as ssock:
        ssock.settimeout(SOCKET_CONN_TIMEOUT)

        while not shutdown_signal.is_set():
            try:
                conn, addr = ssock.accept()

                threading.Thread(
                    target=handle_client,
                    args=(conn, addr, event_stream),
                ).start()
            except ConnectionAbortedError:
                event_stream.push(SystemEvent(SystemEvent.USR_DISCONN_ABT))
            except TimeoutError:
                pass


def handle_client(
    conn: ssl.SSLSocket,
    addr: tuple[str, int],
    event_stream: AppEventStream,
) -> None:
    connection_id = hash(conn)

    event_stream.push(SystemEvent(SystemEvent.USR_CONN_OK, connection_id))

    with conn:
        buffer = ""

        while True:
            print("reading")
            chunk = conn.recv(BUFFER_SIZE).decode()  # blocking
            if not chunk:
                break

            buffer += chunk

            dataBlock = None
            if "\0" in buffer:
                dataBlock, buffer = buffer.split("\0", 1)

            if dataBlock:
                event = UserMessageEvent(dataBlock)
                event_stream.push(event)

    event_stream.push(SystemEvent(SystemEvent.USR_DISCONN_OK, connection_id))
