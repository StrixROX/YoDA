import argparse

from .server import start_core_server
from cli.user_input import start_interactive_mode


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
