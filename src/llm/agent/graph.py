from typing import Annotated, TypedDict

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph, Runnable
from langgraph.prebuilt import ToolNode, tools_condition

from app_streams.events import AppEventStream


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    event_stream: AppEventStream


def create_graph(
    llm: Runnable[LanguageModelInput, BaseChatMessageHistory],
    tools: list[BaseTool],
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    graph_builder = StateGraph(AgentState)

    def chatbot(state: AgentState):
        prompt = ChatPromptTemplate.from_messages(state["messages"])
        chain = prompt | llm

        response = chain.invoke({"messages": state["messages"]})

        return {"messages": state["messages"] + [response]}

    tools_node = ToolNode(tools=tools)

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tools_node)

    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")

    graph = graph_builder.compile()

    return graph
