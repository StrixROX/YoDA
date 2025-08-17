import argparse
import socket
import ssl
from types import MethodType
from comms import start_cli_server


def start_core_server(args: argparse.Namespace):
    port = args.port
    start_cli_server(port)


def connect_to_core_server(
    args: argparse.Namespace, callback: MethodType
) -> ssl.SSLSocket:
    port = args.port

    ssock, error = None, None

    try:
        context = ssl.create_default_context()

        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # bcz we are using self-signed certs

        sock = socket.create_connection(("localhost", port))
        ssock = context.wrap_socket(sock, server_hostname="localhost")
    except Exception as e:
        error = e

    callback(ssock, error)


def pack_msg(msg):
    return msg.encode() + b"\0"
