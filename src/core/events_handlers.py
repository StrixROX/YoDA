from langchain_core.messages import ChatMessage
from app_streams.events import (
    AppEventStream,
    SystemEvent,
    SystemMessageEvent,
    UserMessageEvent,
)
from windows_toasts import WindowsToaster, Toast

from comms.utils import pack_msg
from core.services import CommsServer
from llm.agent import Agent


def on_core_system_ready(event: SystemEvent, event_stream: AppEventStream):

    if event.message == SystemEvent.CORE_SYS_FINISH:
        core_systems_status = event.data

        startup_greeting = (
            "Welcome! All core systems online!"
            if all(core_systems_status.values())
            else "Welcome! Some core systems are offline."
        )

        toaster = WindowsToaster("YoDA")
        newToast = Toast()
        newToast.text_fields = [event.message]
        toaster.show_toast(newToast)

        print(startup_greeting)

        event_stream.push(SystemMessageEvent(startup_greeting))

    elif event.message in [
        SystemEvent.COMMS_ONLINE,
        SystemEvent.COMMS_OFFLINE,
        SystemEvent.LLM_ONLINE,
        SystemEvent.LLM_OFFLINE,
        SystemEvent.AGENT_ONLINE,
        SystemEvent.AGENT_OFFLINE,
    ]:
        print(f"[ {event.message} ]")
    elif event.message in [
        SystemEvent.USR_CONN_OK,
        SystemEvent.USR_DISCONN_OK,
    ]:
        print(f"[ {event.data} ] {event.message}")


def on_user_message(
    event: UserMessageEvent,
    event_stream: AppEventStream,
    comms_server: CommsServer,
    agent: Agent,
):
    try:
        connection_id = event.data

        response = agent.invoke(
            ChatMessage(role=UserMessageEvent.type, content=event.message)
        )

        comms_server.get_connection_by_id(event.data).send(pack_msg(response))
        event_stream.push(SystemMessageEvent(response, connection_id))
    except Exception as e:
        print(e)
