from langchain_core.messages import BaseMessage, ChatMessage
from app_streams.events import AppEvent


def convert_to_base_messages(
    messages: list[AppEvent] | list[BaseMessage],
) -> list[BaseMessage]:
    parsed_messages = []
    for message in messages:
        if isinstance(message, BaseMessage):
            parsed_messages.append(message)
        elif isinstance(message, AppEvent):
            parsed_messages.append(ChatMessage(role=message.type, content=str(message)))

    return parsed_messages
