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


def start_ollama_server(
    callback: Callable[[bool], None], shutdown_signal: threading.Event
) -> subprocess.Popen:
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    def stdout_reader():
        for line in process.stdout:
            if shutdown_signal.is_set():
                break
            if "level=INFO" in line:
                callback(True)
                break
            elif "Error:" in line:
                callback(False)

    def shutdown_monitor():
        shutdown_signal.wait()
        if process.poll() is None:  # Process is still running
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if it doesn't terminate gracefully

    threading.Thread(target=stdout_reader, daemon=True).start()
    threading.Thread(target=shutdown_monitor, daemon=True).start()

    return process


def start_llm_server(
    ollama_port: int,
    event_stream: AppEventStream,
    on_setup: MethodType,
    shutdown_signal: threading.Event,
) -> None:
    ollama_server_base_url = f"http://localhost:{ollama_port}"

    event_stream.push(SystemEvent(SystemEvent.LLM_START, ollama_server_base_url))

    is_server_already_running = check_is_ollama_running(base_url=ollama_server_base_url)

    if is_server_already_running:
        event_stream.push(SystemEvent(SystemEvent.LLM_ONLINE, ollama_server_base_url))
        on_setup(True)
    else:

        def on_subprocess_complete(is_ok: bool):
            event_stream.push(
                SystemEvent(
                    SystemEvent.LLM_ONLINE if is_ok else SystemEvent.LLM_OFFLINE,
                    ollama_server_base_url,
                )
            )
            on_setup(is_ok)

        start_ollama_server(on_subprocess_complete, shutdown_signal)
