import secrets
import threading

from langchain_core.messages import ChatMessage
from langchain_ollama.chat_models import ChatOllama

from app_streams.events import (
    AGENT_OFFLINE,
    AGENT_ONLINE,
    AppEventStream,
    SystemEvent,
)
from core.services import OllamaServer
from llm.agent.graph import create_graph
from llm.agent.memory import AgentPersistentMemory, AgentSessionMemory
from .tools import available_tools

AGENT_SESSION_ID_HEX_SIZE = 16


class Agent:
    def __init__(
        self,
        llm_server: OllamaServer,
        event_stream: AppEventStream,
        shutdown_signal: threading.Event,
    ) -> None:
        self.is_ready = threading.Event()

        self.__ollama_url = llm_server.get_server_url()
        self.__event_stream = event_stream
        self.__shutdown_signal = shutdown_signal

        self.session_id = secrets.token_hex(AGENT_SESSION_ID_HEX_SIZE)

        if llm_server.is_ready.is_set():
            self.__start()
        else:
            self.__on_error(Exception(RuntimeError("Ollama server unavailable.")))

    def __start(self) -> None:
        try:
            # init the llm
            self.__tools = available_tools
            self.__llm = ChatOllama(
                model="qwen3:8b",
                reasoning=False,
                base_url=self.__ollama_url,
                validate_model_on_init=False,
                temperature=0.2,
            ).bind_tools(tools=self.__tools)

            # init llm utilties
            self.__memory = AgentPersistentMemory(
                filepath="data/memory.json"
            )  # primary memory
            self.__session_chat_history = AgentSessionMemory()  # secondary memory

            # init workflow
            self.__graph = create_graph(llm=self.__llm, tools=self.__tools)

            self.__on_ready()

        except Exception as err:
            self.__on_error(err)

    def __on_ready(self):
        self.is_ready.set()

        self.__event_stream.push(
            SystemEvent(
                AGENT_ONLINE,
                {"ollama_url": self.__ollama_url, "session_id": self.session_id},
            )
        )

    def __on_error(self, err: Exception):
        self.__event_stream.push(SystemEvent(AGENT_OFFLINE, {"error": err}))
        print(err)  #

    # def append_to_session_memory(self, messages: list[AppEvent] | list[BaseMessage]):
    #     parsed_messages = self.convert_event_stream_history_to_base_messages(messages)
    #     self.__session_chat_history.update(parsed_messages)

    def invoke(self, user_message: ChatMessage) -> str:
        if not self.is_ready.is_set():
            raise RuntimeError(
                "Agent invoked before initialization. Did you forget to call the setup() method?"
            )

        chat_history = self.__session_chat_history.get()
        print(
            "> querying against:",
            list(map(lambda message: message.content, chat_history)),
        )

        output_state = self.__graph.invoke(
            {
                "messages": chat_history + [user_message],
                "event_stream": self.__event_stream,
                "memory": self.__memory,
            }
        )
        print(
            "> agent returned:",
            list(map(lambda state: state.content, output_state["messages"])),
        )

        new_messages = output_state["messages"][len(chat_history) :]
        print(list(map(lambda msg: msg.content, new_messages)))

        print("> memory write is locked?", self.__session_chat_history.lock.locked())
        self.__session_chat_history.update(new_messages)
        print(
            "> new history:",
            list(
                map(
                    lambda message: message.content,
                    self.__session_chat_history.get(),
                )
            ),
        )

        return new_messages[-1].content
