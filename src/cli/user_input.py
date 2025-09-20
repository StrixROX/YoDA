import argparse
import ssl

from cli.utils import greet, show_loading_text
from comms.client import connect_to_comms_server, listen_for_messages, send_message


def start_interactive_mode(args: argparse.Namespace) -> None:
    greet(heading="YoDA", subHeading="Welcome, you are!")

    stop_loading_text = show_loading_text("Securely connecting to comms server")

    connect_to_comms_server(
        hostname="localhost",
        port=args.port,
        on_done=stop_loading_text,
        on_connect=on_server_connected,
        on_error=lambda err: print(
            "[Error] Unable to connect to comms server. Did you forget to start the comms server?\n"
        ),
    )


def on_server_connected(ssock: ssl.SSLSocket):
    try:
        with ssock:
            print("- Comms server connected\n")

            socket_buffer = ""

            while True:
                prompt = input("> ").strip()
                if prompt == "":
                    continue

                send_message(ssock, prompt)
                message, socket_buffer = listen_for_messages(ssock, socket_buffer)

                print(f"\n{message}\n")

    except ssl.SSLEOFError:
        print("\n[Error] Comms server unavailable. Exiting...")
