import socket
import ssl
from types import MethodType


def connect_to_comms_server(
    port: int, on_connect_callback: MethodType
) -> ssl.SSLSocket:
    ssock, error = None, None

    try:
        context = ssl.create_default_context()

        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # bcz we are using self-signed certs

        sock = socket.create_connection(("localhost", port))
        ssock = context.wrap_socket(sock, server_hostname="localhost")
    except Exception as e:
        error = e

    on_connect_callback(ssock=ssock, error=error)
