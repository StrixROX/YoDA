from collections.abc import Callable
import subprocess
import threading
from types import MethodType

import requests
from app_streams.events import AppEventStream, SystemEvent


def check_is_ollama_running(base_url: str) -> bool:
    ping_endpoint = "/api/version"
    try:
        response = requests.get(f"{base_url}{ping_endpoint}")
        return response.status_code == 200
    except:
        return False


def start_ollama_server(callback: Callable[[bool], None]) -> None:
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    def stdout_reader():
        for line in process.stdout:
            if "level=INFO" in line:
                callback(True)
                break
            elif "Error:" in line:
                callback(False)

    threading.Thread(target=stdout_reader, daemon=True).start()


def start_llm_server(
    event_stream: AppEventStream,
    on_setup: MethodType,
    shutdown_signal: threading.Event,
) -> None:
    base_url = "http://localhost:11434"

    event_stream.push(SystemEvent(SystemEvent.LLM_START, base_url))

    is_server_already_running = check_is_ollama_running(base_url=base_url)

    if is_server_already_running:
        event_stream.push(SystemEvent(SystemEvent.LLM_ONLINE, base_url))
        on_setup(True)
    else:

        def on_subprocess_complete(is_ok: bool):
            event_stream.push(
                SystemEvent(
                    SystemEvent.LLM_ONLINE if is_ok else SystemEvent.LLM_OFFLINE,
                    base_url,
                )
            )
            on_setup(is_ok)

        start_ollama_server(on_subprocess_complete)
