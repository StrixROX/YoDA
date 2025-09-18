import argparse

from core.main import start_core_system

from .user_input import start_interactive_mode


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
    parser.add_argument("-p", "--port", type=int, default=1234, help="comms server port to connect to")
    parser.set_defaults(func=start_interactive_mode)

    commands = parser.add_subparsers(dest="command", title="Supported Commands")

    start_parser = commands.add_parser("start", help="start the core server")
    start_parser.add_argument("-pc", "--port-comms", type=int, default=1234, help="local port for comms server")
    start_parser.add_argument("-po", "--port-ollama", type=int, default=11434, help="local port for ollama server")
    start_parser.set_defaults(func=start_core_system)

    return parser
