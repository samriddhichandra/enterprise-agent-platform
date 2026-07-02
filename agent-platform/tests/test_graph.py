"""
Unit tests for the agent graph's routing logic.

These test the deterministic parts of graph.py (state shape, routing
function) without calling the real OpenAI API, so they run fast and free.
"""
from backend.agents.graph import route_after_planner, AgentState


def make_state(route: str) -> AgentState:
    return {
        "question": "test question",
        "plan": "test plan",
        "route": route,
        "retrieved_chunks": [],
        "tool_used": "",
        "tool_output": "",
        "answer": "",
    }


def test_routes_to_research_when_planner_picks_docs():
    state = make_state(route="research")
    assert route_after_planner(state) == "research"


def test_routes_to_tool_when_planner_picks_tool():
    state = make_state(route="tool")
    assert route_after_planner(state) == "tool"


def test_routes_to_direct_answer_when_planner_picks_direct():
    state = make_state(route="direct")
    assert route_after_planner(state) == "direct_answer"
