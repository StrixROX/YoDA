from types import MethodType


def system_speak(text_content: str, on_complete_callback: MethodType) -> None:
    error = None

    if error:
        return on_complete_callback(success=False, error=error)

    print(f"Speaking: {text_content}")

    return on_complete_callback(success=True, error=None)
