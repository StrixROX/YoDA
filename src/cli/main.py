import argparse
import ssl
import threading
import time
from typing import Union

from comms.client import pack_msg

from .server import (
    start_core_server,
    connect_to_core_server,
    send_message_to_core_server,
)
from .utils import greet


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n--- Session terminated by user ---")
        pass


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yo", description="Centralised System Automations with LLM"
    )
    parser.add_argument("-p", "--port", type=int, default=1234)
    parser.set_defaults(func=start_interactive_mode)

    commands = parser.add_subparsers(
        dest="command", title="Supported Commands", description="asd"
    )

    start_parser = commands.add_parser(
        "start", help="Start the core server", aliases=["i"]
    )
    start_parser.set_defaults(func=start_core_server)

    return parser


def start_interactive_mode(args: argparse.Namespace) -> None:
    greet(heading="YoDA", subHeading="Welcome, you are!")

    _ssock, _error = None, None

    def connection_callback(ssock: ssl.SSLSocket, error: Union[None, Exception]):
        nonlocal _ssock, _error
        _ssock, _error = ssock, error

    connection_thread = threading.Thread(
        target=connect_to_core_server, args=(args, connection_callback)
    )

    connection_thread.start()

    loading_text = "Securely connecting to core server"
    i = 0
    while not _ssock and not _error:
        dots = "." * (i % 4) + " " * (3 - i % 4)
        print("\r" + loading_text + dots, end="", flush=True)
        time.sleep(0.5)
        i += 1

    connection_thread.join()
    print("\033[2K\r", end="", flush=True)  # clear "Loading..." line

    if _error:
        print(
            "[Error] Unable to connect to core server. Did you forget to start the core server?\n"
        )

        return
    else:
        print("- Core server connected\n")

    with _ssock:
        while True:
            prompt = input("> ")

            send_message_to_core_server(prompt, _ssock)
