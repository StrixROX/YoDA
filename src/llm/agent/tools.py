from datetime import datetime
import random
from typing import Annotated
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app_streams.events import SystemEvent
from llm.agent.utils import convert_to_base_messages

from typing import Optional


@tool
def search_memory_segments(
    query: str,
    state: Annotated[dict, InjectedState],
) -> list[dict]:
    """
    Search persistent memory segments by query against name/description.
    Returns a list of segment dicts.
    """
    memory = state.get("memory")
    if memory is None:
        return []
    return memory.find_segments(query)


@tool
def add_memory_segment(
    segment_id: str,
    name: str,
    description: str,
    data: dict,
    state: Annotated[dict, InjectedState],
) -> dict:
    """
    Add a new memory segment. Overwrites if the id already exists.
    Returns the stored segment.
    """
    memory = state.get("memory")
    if memory is None:
        return {
            "error": "memory_not_available",
            "message": "No AgentPersistentMemory available in state under key 'memory'",
        }
    segment = {
        "id": segment_id,
        "name": name,
        "description": description,
        "data": data,
    }
    memory.add_segment(segment)
    return segment


@tool
def update_memory_segment(
    segment_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    data: Optional[dict] = None,
    state: Annotated[dict, InjectedState] = None,
) -> dict:
    """
    Update an existing memory segment's fields. Provide any of name/description/data.
    Returns the updated segment, or an error if not found.
    """
    memory = None if state is None else state.get("memory")
    if memory is None:
        return {
            "error": "memory_not_available",
            "message": "No AgentPersistentMemory available in state under key 'memory'",
        }
    existing = memory.get_segment_by_id(segment_id)
    if existing is None:
        return {"error": "not_found", "message": f"Segment '{segment_id}' not found"}

    updated = dict(existing)
    if name is not None:
        updated["name"] = name
    if description is not None:
        updated["description"] = description
    if data is not None:
        updated["data"] = data

    memory.add_segment(updated)
    return updated


@tool
def persist_memory_to_disk(
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Persist current memory state to disk explicitly.
    Returns a status string.
    """
    memory = state.get("memory")
    if memory is None:
        return "memory_not_available"

    try:
        memory.save()
        return "saved"
    except Exception as e:
        return f"error: {e}"


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


available_tools = [
    count_trees,
    get_current_datetime,
    get_system_events_history,
    search_memory_segments,
    add_memory_segment,
    update_memory_segment,
    persist_memory_to_disk,
]
