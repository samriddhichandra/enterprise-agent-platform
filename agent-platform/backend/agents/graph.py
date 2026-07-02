"""
Core agent orchestration, built with LangGraph.

Three agents collaborate through a shared state object, routed by a
Planner:

    Planner Agent  -> decides ONE of: needs document lookup, needs a tool
                       (calculator/SQL), or can be answered directly
    Research Agent -> retrieves relevant chunks from the RAG pipeline
                       (ChromaDB) and drafts an answer grounded in them
    Tool Agent     -> picks calculator or SQL based on the question, runs
                       it, and drafts an answer from the tool's output

The graph has one entry point and three possible paths, each easy to
trace and explain:

    START -> planner -> (needs_docs)  -> research      -> END
                      -> (needs_tool) -> tool_agent     -> END
                      -> (else)       -> direct_answer  -> END
"""
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from backend.config import settings
from backend.rag.pipeline import rag_pipeline
from backend.tools.calculator import calculate
from backend.tools.sql_tool import run_sql_query

llm = ChatOpenAI(
    model=settings.model_name,
    temperature=settings.temperature,
    openai_api_key=settings.openai_api_key,
)


class AgentState(TypedDict):
    question: str
    plan: str
    route: str  # "research" | "tool" | "direct"
    retrieved_chunks: list[dict]
    tool_used: str
    tool_output: str
    answer: str


PLANNER_PROMPT = """You are a planning agent for an enterprise assistant.
Decide how to answer the user's question. Choose exactly one route:

- DOCS: the question needs internal documents (policies, reports, manuals)
- TOOL: the question needs a calculation (math) or a lookup against the
  employees or orders database (e.g. headcount, order counts, revenue)
- DIRECT: the question can be answered directly with general knowledge

Respond in exactly this format:
ROUTE: DOCS|TOOL|DIRECT
PLAN: <one short sentence describing your plan>

Question: {question}
"""

DIRECT_ANSWER_PROMPT = """You are a helpful enterprise assistant.
Answer the user's question directly and concisely.

Question: {question}
"""

RESEARCH_ANSWER_PROMPT = """You are a helpful enterprise assistant answering
questions using retrieved internal documents. Only use the provided context.
If the context doesn't contain the answer, say so honestly.

Context:
{context}

Question: {question}

Answer, and mention which source(s) you used:
"""

TOOL_SELECT_PROMPT = """You are a Tool Agent. Given a question, decide which
tool to use and produce its exact input.

Available tools:
- calculator: takes a plain arithmetic expression, e.g. "42 * 7"
- sql: takes a single read-only SQL SELECT query against these tables:
    employees(id, name, department)
    orders(id, customer_name, amount, status)

Respond in exactly this format:
TOOL: calculator|sql
INPUT: <the exact expression or SQL query to run>

Question: {question}
"""

TOOL_ANSWER_PROMPT = """You are a helpful enterprise assistant. You used the
{tool_name} tool to help answer the user's question. Turn the raw tool
output below into a clear, natural-language answer.

Question: {question}
Tool output:
{tool_output}

Answer:
"""


def planner_node(state: AgentState) -> AgentState:
    """Decides which of the three routes (docs / tool / direct) to take."""
    prompt = PLANNER_PROMPT.format(question=state["question"])
    response = llm.invoke(prompt).content

    route_line = response.split("ROUTE:")[-1].split("\n")[0].strip().upper() if "ROUTE:" in response else "DIRECT"
    plan_line = response.split("PLAN:")[-1].strip() if "PLAN:" in response else response.strip()

    if "DOCS" in route_line:
        route = "research"
    elif "TOOL" in route_line:
        route = "tool"
    else:
        route = "direct"

    return {**state, "route": route, "plan": plan_line}


def research_node(state: AgentState) -> AgentState:
    """Retrieves relevant chunks from Chroma and drafts a grounded answer."""
    chunks = rag_pipeline.retrieve(state["question"])
    context = "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks) or "No matching documents found."

    prompt = RESEARCH_ANSWER_PROMPT.format(context=context, question=state["question"])
    answer = llm.invoke(prompt).content

    return {**state, "retrieved_chunks": chunks, "answer": answer}


def tool_node(state: AgentState) -> AgentState:
    """Picks a tool (calculator or SQL), runs it, and drafts an answer."""
    select_prompt = TOOL_SELECT_PROMPT.format(question=state["question"])
    selection = llm.invoke(select_prompt).content

    tool_name = selection.split("TOOL:")[-1].split("\n")[0].strip().lower() if "TOOL:" in selection else "calculator"
    tool_input = selection.split("INPUT:")[-1].strip() if "INPUT:" in selection else state["question"]

    if "sql" in tool_name:
        tool_name = "sql"
        tool_output = run_sql_query(tool_input)
    else:
        tool_name = "calculator"
        tool_output = calculate(tool_input)

    answer_prompt = TOOL_ANSWER_PROMPT.format(
        tool_name=tool_name, question=state["question"], tool_output=tool_output
    )
    answer = llm.invoke(answer_prompt).content

    return {**state, "tool_used": tool_name, "tool_output": tool_output, "answer": answer}


def direct_answer_node(state: AgentState) -> AgentState:
    """Answers directly without document retrieval or tools."""
    prompt = DIRECT_ANSWER_PROMPT.format(question=state["question"])
    answer = llm.invoke(prompt).content
    return {**state, "retrieved_chunks": [], "answer": answer}


def route_after_planner(state: AgentState) -> Literal["research", "tool", "direct_answer"]:
    if state["route"] == "research":
        return "research"
    if state["route"] == "tool":
        return "tool"
    return "direct_answer"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("research", research_node)
    graph.add_node("tool", tool_node)
    graph.add_node("direct_answer", direct_answer_node)

    graph.set_entry_point("planner")
    graph.add_conditional_edges("planner", route_after_planner, {
        "research": "research",
        "tool": "tool",
        "direct_answer": "direct_answer",
    })
    graph.add_edge("research", END)
    graph.add_edge("tool", END)
    graph.add_edge("direct_answer", END)

    return graph.compile()


# Compiled graph, ready to invoke from the API layer
agent_graph = build_graph()


def run_agent(question: str) -> AgentState:
    initial_state: AgentState = {
        "question": question,
        "plan": "",
        "route": "",
        "retrieved_chunks": [],
        "tool_used": "",
        "tool_output": "",
        "answer": "",
    }
    return agent_graph.invoke(initial_state)
