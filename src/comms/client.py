import socket
import ssl
from typing import Callable, Tuple

from comms.utils import pack_msg

BUFFER_SIZE = 1024


def connect_to_comms_server(
    hostname: str,
    port: int,
    on_connect: Callable[[ssl.SSLSocket], None],
    on_error: Callable[[Exception], None],
    on_done: Callable[[], None],
) -> None:
    try:
        context = ssl.create_default_context()

        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # bcz we are using self-signed certs

        sock = socket.create_connection((hostname, port))
        ssock = context.wrap_socket(sock, server_hostname=hostname)
        ssock.setblocking(False)

        on_done()
        on_connect(ssock)
    except Exception as e:
        on_done()
        on_error(e)


def send_message(ssock: ssl.SSLSocket, message: str) -> None:
    # assuming opening and closing the ssock is handled externally
    parsed_message = message.strip()
    if parsed_message == "":
        return

    ssock.sendall(pack_msg(parsed_message))


def listen_for_messages(ssock: ssl.SSLSocket, init_buffer: str = "") -> Tuple[str, str]:
    # assuming opening and closing the ssock is handled externally
    buffer = init_buffer

    ssock.setblocking(True)

    while "\0" not in buffer:
        chunk = ""

        try:
            chunk = ssock.recv(BUFFER_SIZE).decode()
            chunk = None if chunk == "" else chunk
        except ssl.SSLWantReadError:
            pass

        if chunk is None:
            break

        buffer += chunk

    message, remainder = buffer.split("\0", 1)

    return message, remainder
