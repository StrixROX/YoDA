import argparse
import ssl
import threading
import time
from typing import Union

from cli.server import connect_to_core_server, send_message_to_core_server
from cli.utils import greet


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

    try:
        with _ssock:
            while True:
                prompt = input("> ")

                send_message_to_core_server(prompt, _ssock)
    except ssl.SSLEOFError:
        print("\n[Error] Core system unavailable. Exiting...")