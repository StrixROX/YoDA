from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, ChatMessage
from langchain_core.runnables import Runnable
from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from windows_toasts import WindowsToaster, Toast

from llm.agent import Agent


# LLM calls on system events will go here
def system_event_handler(
    event: SystemEvent, event_stream: AppEventStream, agent: Agent
) -> None:
    if event.message == SystemEvent.LLM_ONLINE:
        agent.setup()

    elif event.message == SystemEvent.CORE_SYS_FINISH:
        core_systems_status = event.data

        startup_greeting = (
            "Welcome! All core systems online!"
            if all(core_systems_status.values())
            else "Welcome! Some core systems are offline."
        )

        event_stream.push(SystemMessageEvent(startup_greeting))


# TTS/GUI Render calls will go here
def system_message_handler(
    event: SystemMessageEvent,
    event_stream: AppEventStream,
) -> None:
    # toaster = WindowsToaster("YoDA")
    # newToast = Toast()
    # newToast.text_fields = [event.message]
    # toaster.show_toast(newToast)
    print(event.message)


# LLM calls on user input will go here
def user_message_handler(
    event: UserMessageEvent, event_stream: AppEventStream, agent: Agent
) -> None:
    session_id = agent.session_id
    config = {"configurable": {"thread_id": session_id}}

    response = agent.graph.invoke(
        {"messages": [ChatMessage(role=UserMessageEvent.type, content=event.message)]},
        config,
    )
    event_stream.push(SystemMessageEvent(response["messages"][-1].content))
