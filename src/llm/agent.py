from datetime import datetime
import random
import threading
from typing import Annotated, TypedDict
from langchain_core.messages import (
    AnyMessage,
    BaseMessage,
    ChatMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from app_streams.events import AppEventStream, SystemEvent
from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import secrets

AGENT_SESSION_ID_HEX_SIZE = 16


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class AgentSessionMemory:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._history: list[BaseMessage] = []

    def get(self):
        return [*self._history]

    def update(self, messages: list[BaseMessage]) -> None:
        print("-> about to update history")
        with self.lock:
            print("-> acquired lock")
            self._history += messages
            print("-> history updated. releasing lock...")
        print("-> lock released")


class Agent:
    def __init__(self, ollama_url: str, event_stream: AppEventStream = None):
        self.ollama_url = ollama_url
        self.event_stream = event_stream
        self.is_ready = False

        self.session_id = None

        self.llm = None
        self.tools = []
        self.graph = None
        self.session_chat_history = AgentSessionMemory()  # secondary memory

    def setup(self):
        try:
            self.init_tools()
            self.init_llm()
            self.init_stategraph()

            self.session_id = secrets.token_hex(AGENT_SESSION_ID_HEX_SIZE)
            self.event_stream.push(
                SystemEvent(
                    SystemEvent.AGENT_ONLINE,
                    {
                        "url": self.ollama_url,
                        "session_id": self.session_id,
                    },
                )
            )
            self.is_ready = True
        except Exception as err:
            if self.event_stream:
                self.event_stream.push(SystemEvent(SystemEvent.AGENT_OFFLINE, err))
            print(err)  # temp

    def init_tools(self):
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

        self.tools = [count_trees, get_current_datetime]

    def init_llm(self):
        llm = ChatOllama(
            model="qwen3:8b",
            reasoning=False,
            base_url=self.ollama_url,
            validate_model_on_init=False,
            temperature=0.2,
        )

        self.llm = llm.bind_tools(tools=self.tools)

    def init_stategraph(self):
        graph_builder = StateGraph(AgentState)

        def chatbot(state: AgentState):            
            prompt = ChatPromptTemplate.from_messages(state["messages"])
            chain = prompt | self.llm
            
            response = chain.invoke({"messages": state["messages"]})

            return {"messages": state["messages"] + [response]}

        tools_node = ToolNode(tools=self.tools)

        graph_builder.add_node("chatbot", chatbot)
        graph_builder.add_node("tools", tools_node)

        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges("chatbot", tools_condition)
        graph_builder.add_edge("tools", "chatbot")

        graph = graph_builder.compile()

        self.graph = graph

    def invoke(self, user_message: ChatMessage):
        if not self.is_ready:
            raise RuntimeError(
                "Agent invoked before initialization. Did you forget to call the setup() method?"
            )

        memory = self.session_chat_history.get()
        print(
            "> querying against:",
            list(map(lambda message: message.content, memory)),
        )

        output_state = self.graph.invoke({"messages": memory + [user_message]})
        print(
            "> agent returned:",
            list(map(lambda state: state.content, output_state["messages"])),
        )

        new_messages = output_state["messages"][len(memory) :]
        print(list(map(lambda msg: msg.content, new_messages)))

        print("> memory write is locked?", self.session_chat_history.lock.locked())
        self.session_chat_history.update(new_messages)
        print(
            "> new history:",
            list(
                map(
                    lambda message: message.content,
                    self.session_chat_history.get(),
                )
            ),
        )

        return new_messages[-1].content
