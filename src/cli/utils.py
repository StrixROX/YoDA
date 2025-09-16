import threading
import time
from types import MethodType
from art import text2art


def greet(heading, subHeading):
    banner = text2art(heading, "sub-zero") if heading else None
    bannerWidth = banner.index("\n") if heading else None

    greeting = f"--- {subHeading} ---"
    paddedGreeting = f"{greeting:^{bannerWidth}}" if heading else greeting

    if banner:
        print(banner)

    if paddedGreeting:
        print(paddedGreeting + "\n")


def show_loading_text(loading_text="Loading") -> MethodType:
    is_process_complete = threading.Event()

    def print_text():
        nonlocal is_process_complete
        print(end="", flush=True)

        i = 0
        while not is_process_complete.is_set():
            dots = "." * (i % 4) + " " * (3 - i % 4)
            print("\r" + loading_text + dots, end="", flush=True)
            time.sleep(0.5)
            i += 1
        print("\033[2K\r", end="", flush=True)  # clear "Loading..." line

    print_text_thread = threading.Thread(target=print_text)

    def stop():
        nonlocal is_process_complete
        is_process_complete.set()
        print_text_thread.join()

    print_text_thread.start()

    return stop
