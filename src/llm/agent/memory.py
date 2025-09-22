import json
import os
import threading
from typing import Optional

from langchain_core.messages import BaseMessage


class AgentSessionMemory:
    def __init__(self, init_history: list[BaseMessage] = []) -> None:
        self.lock = threading.Lock()
        self._history: list[BaseMessage] = init_history

    def get(self):
        return [*self._history]

    def update(self, messages: list[BaseMessage]) -> None:
        # print("-> about to update history")
        with self.lock:
            # print("-> acquired lock")
            self._history += messages
            # print("-> history updated. releasing lock...")
        # print("-> lock released")


class AgentPersistentMemory:
    """
    Thread-safe persistent memory for LLM agents.
    Stores memory as a list of JSON-like objects ("segments").
    Each segment has at least: { "id": str, "name": str, "description": str, "data": dict }
    """

    def __init__(self, filepath: str = "memory.json") -> None:
        self.filepath = filepath
        self.lock = threading.RLock()
        self.memory: list[dict[str, any]] = []
        self.__load()

    def __load(self) -> None:
        """Load memory from disk if available."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.memory = []

    def save(self) -> None:
        """Persist memory to disk. Ensures parent directory exists."""
        parent_dir = os.path.dirname(self.filepath)

        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def add_segment(self, segment: dict[str, any]) -> None:
        """
        Add a memory segment.
        Expected keys: id (unique), name, description, data
        """
        with self.lock:
            # overwrite if same id exists
            self.memory = [s for s in self.memory if s.get("id") != segment.get("id")]
            self.memory.append(segment)
            self.save()

    def get_segment_by_id(self, segment_id: str) -> Optional[dict[str, any]]:
        """Retrieve a memory segment by ID."""
        with self.lock:
            return next((s for s in self.memory if s.get("id") == segment_id), None)

    def find_segments(self, query: str) -> list[dict[str, any]]:
        """
        Naive search: return segments whose name/description contain query.
        """
        with self.lock:
            return [
                s
                for s in self.memory
                if query.lower() in s.get("name", "").lower()
                or query.lower() in s.get("description", "").lower()
            ]

    def delete_segment(self, segment_id: str) -> bool:
        """Delete a memory segment by ID. Returns True if deleted."""
        with self.lock:
            before = len(self.memory)
            self.memory = [s for s in self.memory if s.get("id") != segment_id]
            if len(self.memory) < before:
                self.save()
                return True
            return False

    def list_segments(self) -> list[dict[str, any]]:
        """Return all segments."""
        with self.lock:
            return list(self.memory)
