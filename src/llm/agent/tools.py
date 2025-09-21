from datetime import datetime
import random
from typing import Annotated
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app_streams.events import SystemEvent
from llm.agent.utils import convert_to_base_messages


@tool
def count_trees(name: str) -> int:
    """
    Count the number of trees in a forest. Takes name of the forest as argument.
    The number of trees in any area changes frequently. Do not use outdated values.
    """
    return random.randint(20, 100) if "elder" in name else 23


@tool
def get_current_datetime() -> str:
    """
    Get current system date and time, including milliseconds.
    When asked for time, return only the time to user in AM/PM.
    When asked for date, return only date to the user.
    When asked for day, return only day to the user.
    """
    return datetime.now().strftime("%A %Y-%m-%d %H:%M:%S.%f")


@tool
def get_system_events_history(
    state: Annotated[dict, InjectedState],
) -> list[BaseMessage]:
    """
    Get the history of system events that have happened since system start.
    This typically includes the status of system services and user connections.
    """

    messages = [
        event
        for event in list(state["event_stream"].history)
        if isinstance(event, SystemEvent)
    ]
    parsed_messages = convert_to_base_messages(messages)

    return parsed_messages


available_tools = [count_trees, get_current_datetime, get_system_events_history]
