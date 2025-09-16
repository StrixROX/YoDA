import argparse
import ssl

from cli.utils import greet, show_loading_text
from comms.client import connect_to_comms_server, listen_for_messages, send_message


def start_interactive_mode(args: argparse.Namespace) -> None:
    greet(heading="YoDA", subHeading="Welcome, you are!")

    stop_loading_text = show_loading_text("Securely connecting to comms server")

    ssock = connect_to_comms_server(
        port=args.port, on_complete_callback=stop_loading_text
    )[0]

    if ssock:
        try:
            with ssock:
                print("- Comms server connected\n")

                on_server_connected(ssock)

        except ssl.SSLEOFError:
            print("\n[Error] Comms server unavailable. Exiting...")
    else:
        print(
            "[Error] Unable to connect to comms server. Did you forget to start the comms server?\n"
        )


def on_server_connected(ssock: ssl.SSLSocket):
    def on_response(message: str):
        print(f"\n{message}\n")

    while True:
        prompt = input("> ").strip()
        if prompt == "":
            continue

        send_message(ssock, prompt)
        listen_for_messages(ssock, on_response)
