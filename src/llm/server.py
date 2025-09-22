from collections.abc import Callable
import subprocess

import requests


def get_is_ollama_server_running(base_url: str) -> bool:
    ping_endpoint = "/api/version"
    try:
        response = requests.get(f"{base_url}{ping_endpoint}")
        return response.status_code == 200
    except:
        return False


def start_ollama_server(
    on_start: Callable[[subprocess.Popen], None],
    on_done: Callable[[], None],
    on_error: Callable[[Exception], None],
) -> None:
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in process.stdout:
        if "level=INFO" in line:
            on_done()
            on_start(process)
            break
        elif "Error:" in line:
            on_done()
            on_error(Exception(line))
            break
