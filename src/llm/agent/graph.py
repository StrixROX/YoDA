from typing import Annotated, Literal, TypedDict

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AnyMessage, ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from langchain_ollama.chat_models import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph, Runnable
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

from langchain_core.vectorstores import VectorStore

from app_streams.events import AppEventStream
from llm.agent.memory import AgentPersistentMemory


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    event_stream: AppEventStream
    memory: AgentPersistentMemory


class AnalyzerModelSchema(BaseModel):
    """
    Selects the appropriate workflow that needs to be used to answer a user query.
    - Read system events
    - Read memory
    - DEFAULT (none of the above)
    """

    workflow: Literal[
        "read_system_events",
        "read_memory",
        "DEFAULT",
    ] = Field(..., description="the workflow that the user request should be routed to")


ANALYZER_SYSTEM_PROMPT = """
You are an expert at routing a user's request to an appropriate workflow.
The following workflows are available (with descriptions) for routing:
- read_system_events: if additional information is needed about the system, core services or system events that have occured, to respond in the most up to date and accurate way possible at the moment. There are 3 core services: comms_server, llm_server and agent.
- read_memory: if additional information is needed from previous interactions to respond in the most accurate way possible at the moment or if any previously undefined word/noun is referenced by the user, choose this workflow.
- DEFAULT: ONLY if NONE of the above workflows are relevant, return this.
"""


def init_analyzer_llm(ollama_url: str):
    llm = ChatOllama(
        model="qwen3:8b",
        reasoning=False,
        base_url=ollama_url,
        validate_model_on_init=False,
        temperature=0,
        keep_alive=True,
    )

    llm_with_structured_output = llm.with_structured_output(
        schema=AnalyzerModelSchema,
        method="json_schema",
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", ANALYZER_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )

    analyzer = prompt_template | llm_with_structured_output

    return analyzer


class BinaryGraderModelSchema(BaseModel):
    """
    Binary 'yes' or 'no' output based on relevancy of a list of documents to a give query
    """

    binary_score: Literal["yes", "no"] = Field(
        ...,
        description="is the document is relevant to the user query, 'yes' or 'no'?",
    )


BINARY_GRADER_PROMPT = """
You are a grader assessing relevance of a retrieved documment to a user query.
If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the query.
"""


def init_binary_grader_llm(
    ollama_url: str,
):
    llm = ChatOllama(
        model="deepseek-r1:8b",
        reasoning=False,
        base_url=ollama_url,
        validate_model_on_init=False,
        temperature=0,
        keep_alive=True,
    )

    llm_with_structured_output = llm.with_structured_output(
        schema=BinaryGraderModelSchema, method="json_schema"
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", BINARY_GRADER_PROMPT),
            (
                "human",
                "Document Metadata:\n\n{metadata}\n\nDocument:\n\n{document}\n\nUser query: {query}",
            ),
        ]
    )

    binary_document_grader = prompt_template | llm_with_structured_output

    return binary_document_grader


def init_embedding_model(ollama_url: str):
    return OllamaEmbeddings(
        model="nomic-embed-text",
        keep_alive=True,
    )


class QuerySummarizerModelSchema(BaseModel):
    """
    summarizes the chat history to a single user query.
    """

    query: str = Field(
        ...,
        description="concise and accurate summary of the user's query as implied by the chat history",
    )


# QUERY_SUMMARIZER_PROMPT = """
# Based on the provided chat history (newest last), summarise the user's request in a concise and accurate manner. preserve all keywords, nouns and logic.
# """
# QUERY_SUMMARIZER_PROMPT = """
# You are given a multi-turn conversation between a user and an assistant.
# Your task is to rewrite the final user message so that it is fully self-contained.
# Resolve all pronouns, vague references (e.g., "this", "that", "it", "they", "above"),
# and context-dependent phrases by replacing them with the actual keywords or phrases
# from earlier in the conversation.

# Output only a single concise sentence that preserves the exact intent of the final user message.
# Do not add new information, explanations, or responses — just rewrite the message clearly.
# """ # output = "hi there is the server running"
# QUERY_SUMMARIZER_PROMPT = """
# You are given a multi-turn conversation between a user and an assistant.
# Your task is to rewrite ONLY the final user message so that it becomes a fully self-contained query or statement.

# - If the last user message contains vague references (e.g., "this", "that", "it", "they", "above"), replace them with the appropriate words or phrases from earlier in the conversation.
# - If the last user message is already self-contained, output it exactly as it is.
# - Do not include greetings or earlier context unless directly referenced.
# - Output only the rewritten last user message, nothing else.
# """  # output = ""
# QUERY_SUMMARIZER_PROMPT = """
# You are given a conversation between a user and an assistant.
# Your task is to rewrite ONLY the final user message so that it becomes a fully self-contained query or statement.

# - Use the provided supporting chat context ONLY to resolve vague references in the last user message (such as "this", "that", "it", "they", or "above").
# - If the last user message is already self-contained, leave it unchanged.
# - Do not include greetings, small talk, or unrelated context.
# - Do not add explanations or responses — output only the rewritten message.
# - Output must strictly follow the JSON schema provided.
# """  # output = ""
# QUERY_SUMMARIZER_PROMPT = """
# You are given a conversation between a user and an assistant.

# Generate four factual points summarizing the key context from the entire conversation and generate a final concise summary of the question being asked in the last user message..
# Make sure that:
# - Each point must be a standalone fact.
# - Use neutral, factual language.
# - Do not include speculation or irrelevant greetings.

# Guidelines:
# - The factual points should include both the user's intent and the assistant's responses where relevant.
# - The summary must restate the last user message clearly, resolving any vague references (e.g., "this", "that", "it") using the chat context.
# - Output should be a single string
# """  # output = ""


# def init_query_summarizer(ollama_url: str):
#     llm = ChatOllama(
#         model="deepseek-r1:8b",
#         reasoning=False,
#         base_url=ollama_url,
#         validate_model_on_init=False,
#         temperature=0,
#         keep_alive=True,
#     )

#     llm_with_structured_output = llm.with_structured_output(
#         schema=QuerySummarizerModelSchema,
#         method="json_schema",
#     )

#     prompt_template = ChatPromptTemplate.from_messages(
#         [
#             ("system", QUERY_SUMMARIZER_PROMPT),
#             (
#                 "human",
#                 "User message: {user_message}\n\nSupporting chat context: {chat_context}",
#             ),
#         ]
#     )

#     query_summarizer = prompt_template | llm_with_structured_output

#     return query_summarizer


def create_graph(
    analyzer_llm: RunnableSerializable[dict, dict | BaseModel],
    binary_document_grader_llm: RunnableSerializable[dict, dict | BaseModel],
    # query_summarizer_llm: RunnableSerializable[dict, dict | BaseModel],
    memory_vector_store: VectorStore,
    system_events_vector_store: VectorStore,
    llm: Runnable[LanguageModelInput, BaseChatMessageHistory],
    tools: list[BaseTool],
) -> CompiledStateGraph[AgentState, None, AgentState, AgentState]:
    graph_builder = StateGraph(AgentState)

    def chatbot(state: AgentState):
        prompt = ChatPromptTemplate.from_messages(state["messages"])
        chain = prompt | llm

        response = chain.invoke(
            {
                "messages": [
                    (
                        "system",
                        "If the user tells you to remember something, always use the update_memory tool.",
                    )
                ]
                + state["messages"]
            }
        )

        return {"messages": state["messages"] + [response]}

    QUESTION_CHAT_CONTEXT_SIZE = 1  # this can be made dynamic

    def analyzer(state: AgentState):
        """
        Route question to the appropriate workflow:
        - Read system events
        - Read memory
        - DEFAULT (None of the above)
        """

        # add in a bit of chat context, so let's take last like 10 messages
        question_with_chat_context = state["messages"][-QUESTION_CHAT_CONTEXT_SIZE:]

        # temp
        print("analyzing question...")

        relevant_workflow: AnalyzerModelSchema = analyzer_llm.invoke(
            {"messages": question_with_chat_context}
        )

        # temp
        print("going to", relevant_workflow.workflow)

        return relevant_workflow.workflow

    def get_binary_relevance_scores(
        docs: list[Document],
        query: str,
    ) -> list[tuple[Document, int]]:
        """
        Get a binary relevance score for a list of documents against a query.
        """

        binary_relevance_scores = [
            (
                doc,
                binary_document_grader_llm.invoke(
                    {
                        "metadata": doc.metadata,
                        "document": doc.page_content,
                        "query": query,
                    }
                ).binary_score,
            )
            for doc in docs
        ]

        return binary_relevance_scores

    def search_source(
        source: VectorStore,
        query: str,
        k: int = 5,
        iterations: int = 0,
    ) -> list[Document]:
        """
        Repeatedly search through a datasource with increasing 'k' until an irrelevant data point is retrieved.
        Then filter out the irrelevant data points and return all the relevant data points.

        Useful when ALL the relevant data points are needed.
        """

        print(f"searching... (k={k}, iterations={iterations})")

        DEL_K = 5 + 5 * iterations  # incremental increase in k

        similar_docs = source.similarity_search(query, k=k)
        docs_with_binary_relevance_score = get_binary_relevance_scores(
            similar_docs, query
        )
        print(*docs_with_binary_relevance_score, sep="\n")
        relevant_docs = [
            doc
            for doc, binary_score in docs_with_binary_relevance_score
            if binary_score == "yes"
        ]

        if len(relevant_docs) == k:
            return search_source(source, query, k + DEL_K, iterations + 1)
        else:
            return relevant_docs

    def read_system_events(state: AgentState):
        """Adds relevant system events to state and generates response from agent LLM"""
        # query = "\n".join(
        #     [
        #         (
        #             f"{message.role}: {message.content}"
        #             if isinstance(message, ChatMessage)
        #             else f"assistant: {message.content}"
        #         )
        #         for message in state["messages"][-QUESTION_CHAT_CONTEXT_SIZE:]
        #     ]
        # )
        query = state["messages"][-1].content

        # temp
        print("query summary:\n", query)
        print("searching for relevant system events...")

        relevant_docs = search_source(
            source=system_events_vector_store,
            query=query,
        )
        relevant_docs_content = list(map(lambda x: x.page_content, relevant_docs))

        new_context_message = (
            ChatMessage(
                role="system",
                content=f"Failed to read system events.",
            )
            if len(relevant_docs_content) == 0
            else ChatMessage(
                role="system",
                content=f"Some relevant system events:\n\n{relevant_docs_content}",
            )
        )

        print("adding context:\n\n", new_context_message.content, "\n")

        response = llm.invoke(state["messages"] + [new_context_message])

        return {
            "messages": state["messages"] + [response],
        }

    def read_memory(state: AgentState):
        """Adds relevant memory segments to state and generates response from agent LLM"""
        # query = "\n".join(
        #     [
        #         (
        #             f"{message.role}: {message.content}"
        #             if isinstance(message, ChatMessage)
        #             else f"assistant: {message.content}"
        #         )
        #         for message in state["messages"][-QUESTION_CHAT_CONTEXT_SIZE:]
        #     ]
        # )
        query = state["messages"][-1].content

        # temp
        print("query summary:\n", query)
        print("searching for relevant memory segments...")

        relevant_docs = search_source(
            source=memory_vector_store,
            query=query,
        )
        relevant_docs_content = list(map(lambda x: x.page_content, relevant_docs))

        new_context_message = (
            ChatMessage(
                role="system",
                content=f"Failed to read memory.",
            )
            if len(relevant_docs_content) == 0
            else ChatMessage(
                role="system",
                content=f"Some relevant segments from memory:\n\n{relevant_docs_content}",
            )
        )

        print("adding context:\n\n", new_context_message.content, "\n")

        response = llm.invoke(state["messages"] + [new_context_message])

        return {
            "messages": state["messages"] + [response],
        }

    tools_node = ToolNode(tools=tools)

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tools_node)
    graph_builder.add_node("read_system_events", read_system_events)
    graph_builder.add_node("read_memory", read_memory)

    graph_builder.set_conditional_entry_point(
        analyzer,
        {
            "read_system_events": "read_system_events",
            "read_memory": "read_memory",
            "DEFAULT": "chatbot",
        },
    )
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")

    graph = graph_builder.compile()

    return graph
