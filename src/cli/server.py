import argparse
import ssl
from types import MethodType
from comms.client import connect_to_comms_server, pack_msg
from core.main import start


def start_core_systems(args: argparse.Namespace) -> None:
    start(comms_port=args.port_comms, ollama_port=args.port_ollama)


def connect_to_core_systems(args: argparse.Namespace, callback: MethodType) -> None:
    connect_to_comms_server(port=args.port, on_connect_callback=callback)


def send_message_to_core_server(message: str, ssock: ssl.SSLSocket) -> None:
    if not message.strip():
        return

    ssock.sendall(pack_msg(message.strip()))
