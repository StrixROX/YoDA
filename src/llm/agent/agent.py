import secrets
import threading

from langchain_core.messages import ChatMessage
from langchain_ollama.chat_models import ChatOllama

from app_streams.events import AppEventStream, SystemEvent
from llm.agent.graph import create_graph
from llm.agent.memory import AgentSessionMemory
from .tools import available_tools

AGENT_SESSION_ID_HEX_SIZE = 16


class Agent:
    def __init__(
        self,
        ollama_url: str,
        event_stream: AppEventStream,
        shutdown_signal: threading.Event,
    ) -> None:
        self.is_ready = threading.Event()

        self.__ollama_url = ollama_url
        self.__event_stream = event_stream
        self.__shutdown_signal = shutdown_signal

        self.session_id = secrets.token_hex(AGENT_SESSION_ID_HEX_SIZE)

        self.__start()

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

            #  init llm utilties
            self.__session_chat_history = AgentSessionMemory()  # secondary memory

            # init workflow
            self.__graph = create_graph(llm=self.__llm, tools=self.__tools)

            self.__event_stream.push(
                SystemEvent(
                    SystemEvent.AGENT_ONLINE,
                    {"url": self.__ollama_url, "session_id": self.session_id},
                )
            )

            self.is_ready.set()

        except Exception as err:
            if self.__event_stream:
                self.__event_stream.push(SystemEvent(SystemEvent.AGENT_OFFLINE, err))
            print(err)  # temp

    def invoke(self, user_message: ChatMessage) -> str:
        if not self.is_ready.is_set():
            raise RuntimeError(
                "Agent invoked before initialization. Did you forget to call the setup() method?"
            )

        memory = self.__session_chat_history.get()
        print(
            "> querying against:",
            list(map(lambda message: message.content, memory)),
        )

        output_state = self.__graph.invoke({"messages": memory + [user_message]})
        print(
            "> agent returned:",
            list(map(lambda state: state.content, output_state["messages"])),
        )

        new_messages = output_state["messages"][len(memory) :]
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
