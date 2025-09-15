import argparse
import ssl
from types import MethodType
from typing import Callable
from comms.client import connect_to_comms_server
from comms.server import BUFFER_SIZE
from comms.utils import pack_msg
from core.main import start


def start_core_systems(args: argparse.Namespace) -> None:
    start(comms_port=args.port_comms, ollama_port=args.port_ollama)


def connect_to_core_systems(args: argparse.Namespace, callback: MethodType) -> None:
    connect_to_comms_server(port=args.port, on_connect_callback=callback)


def send_message_to_core_server(message: str, ssock: ssl.SSLSocket) -> None:
    # assuming opening and closing the ssock is handled externally

    if not message.strip():
        return

    ssock.sendall(pack_msg(message.strip()))


def process_messages_from_core_server(
    handler: Callable[str, None], ssock: ssl.SSLSocket
):
    # assuming opening and closing the ssock is handled externally

    buffer = ""

    while True:

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
