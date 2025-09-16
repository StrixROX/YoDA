import socket
import ssl
from types import MethodType
from typing import Callable, Tuple, Union

from comms.utils import pack_msg

BUFFER_SIZE = 1024


def connect_to_comms_server(
    port: int,
    on_complete_callback: MethodType,
) -> Union[Tuple[ssl.SSLSocket, None, int], Tuple[None, Exception, None]]:
    ssock, error, connection_id = None, None, None

    try:
        context = ssl.create_default_context()

        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # bcz we are using self-signed certs

        sock = socket.create_connection(("localhost", port))
        ssock = context.wrap_socket(sock, server_hostname="localhost")
    except Exception as e:
        error = e

    on_complete_callback()

    return ssock, error, connection_id


def send_message(ssock: ssl.SSLSocket, message: str) -> None:
    # assuming opening and closing the ssock is handled externally
    parsed_message = message.strip()
    if parsed_message == "":
        return

    ssock.sendall(pack_msg(parsed_message))


def listen_for_messages(ssock: ssl.SSLSocket, handler: Callable[str, None]):
    # assuming opening and closing the ssock is handled externally
    buffer = ""

    while True:
        chunk = ""

        try:
            chunk = ssock.recv(BUFFER_SIZE).decode()
            chunk = None if chunk == "" else chunk
        except ssl.SSLWantReadError:
            pass

        if chunk is None:
            break

        buffer += chunk

        if "\0" in buffer:
            break

    handler(buffer.split("\0")[0])
