import argparse
import ssl
import threading
import time
from typing import Union

from .server import pack_msg, start_core_server, connect_to_core_server
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
        prog="YoDA", description="Centralised System Automations with LLM"
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

    ssock, error = None, None

    def connection_callback(_ssock: ssl.SSLSocket, _error: Union[None, Exception]):
        nonlocal ssock, error
        ssock, error = _ssock, _error

    connection_thread = threading.Thread(
        target=connect_to_core_server, args=(args, connection_callback)
    )

    connection_thread.start()

    loading_text = "Securely connecting to core server"
    i = 0
    while not ssock and not error:
        dots = "." * (i % 4) + " " * (3 - i % 4)
        print("\r" + loading_text + dots, end="", flush=True)
        time.sleep(0.5)
        i += 1

    connection_thread.join()
    print('\033[2K\r', end="", flush=True) # clear Loading... line

    if error:
        print(
            "[Error] Unable to connect to core server. Did you forget to start the core server?\n"
        )

        return
    else:
        print("- Core server connected\n")

    with ssock:
        while True:
            prompt = input("> ")

            ssock.sendall(pack_msg(prompt))
