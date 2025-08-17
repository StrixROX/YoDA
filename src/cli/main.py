import argparse
from .utils import greet
from comms import start_cli_server


def main() -> None:
    args = parse_args()

    if args.command:
        args.func(args)
    else:
        greet(heading="YoDA", subHeading="Welcome, you are!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="YoDA", description="Centralised System Automations with LLM"
    )

    commands = parser.add_subparsers(dest="command", title="Supported Commands")

    start_parser = commands.add_parser(
        "start", help="Start the application", aliases=["i"]
    )
    start_parser.add_argument("-p", "--port", type=int, default=1234)
    start_parser.set_defaults(func=start_core_server)

    return parser.parse_args()


def start_core_server(args: argparse.Namespace):
    port = args.port

    start_cli_server(port)
