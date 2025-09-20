from datetime import datetime
import random
from langchain_core.tools import tool


@tool
def count_trees(name: str):
    """
    Count the number of trees in a forest. Takes name of the forest as argument.
    The number of trees in any area changes frequently. Do not use outdated values.
    """
    return random.randint(20, 100) if "elder" in name else 23


@tool
def get_current_datetime():
    """
    Get current system date and time, including milliseconds.
    When asked for time, return only the time to user in AM/PM.
    When asked for date, return only date to the user.
    When asked for day, return only day to the user.
    """
    return datetime.now().strftime("%A %Y-%m-%d %H:%M:%S.%f")


available_tools = [count_trees, get_current_datetime]
