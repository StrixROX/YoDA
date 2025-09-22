import socket
import ssl
import threading
from typing import Callable


BUFFER_SIZE = 1024

CERT_FILE = "server.crt"
KEY_FILE = "server.key"


def start_server(
    hostname: str,
    port: int,
    on_start: Callable[[ssl.SSLSocket], None],
    on_error: Callable[[Exception], None],
    on_done: Callable[[], None] = lambda: None,
) -> None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((hostname, port))
        sock.listen()

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

        ssock = context.wrap_socket(sock, server_side=True)
        ssock.setblocking(True)

        on_done()
        on_start(ssock)

    except Exception as err:
        on_done()
        on_error(err)


def listen_for_connections(
    ssock: ssl.SSLSocket,
    shutdown_signal: threading.Event,
    on_client_connected: Callable[[ssl.SSLSocket, tuple[str, int]], None],
):
    # blocking, connection listener

    while not shutdown_signal.is_set():
        client, addr = ssock.accept()
        client.setblocking(False)

        on_client_connected(client, addr)
    else:
        ssock.close()


def get_is_socket_connected(ssock: ssl.SSLSocket) -> bool:
    try:
        # Attempt to send 0 bytes (non-blocking check)
        ssock.send(b"")
        return True
    except (socket.error, ssl.SSLError):
        return False
