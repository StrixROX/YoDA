import argparse
import ssl
from types import MethodType
from comms.client import connect_to_comms_server, pack_msg
from core.main import start


def start_core_server(args: argparse.Namespace):
    port = args.port
    start(port)


def connect_to_core_server(
    args: argparse.Namespace, callback: MethodType
) -> ssl.SSLSocket:
    port = args.port
    connect_to_comms_server(port, callback)


def send_message_to_core_server(message: str, ssock: ssl.SSLSocket) -> None:
    if not message.strip():
        return

    ssock.sendall(pack_msg(message.strip()))
