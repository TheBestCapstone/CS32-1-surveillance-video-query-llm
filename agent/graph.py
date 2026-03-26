import os
import sys
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from node.answer_node import final_answer_node, final_error_node
from node.parse_node import create_parse_node
from node.route_node import error_router_node, route_by_error
from node.rerank_node import create_rerank_node
from node.sql_node import create_sql_search_node
from node.types import AgentState


def load_env() -> None:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    if not os.getenv("OPENAI_API_KEY") and os.getenv("DASHSCOPE_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")
    if not os.getenv("OPENAI_BASE_URL") and os.getenv("DASHSCOPE_URL"):
        os.environ["OPENAI_BASE_URL"] = os.getenv("DASHSCOPE_URL")


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model_name="qwen3-max",
        temperature=1.0,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_URL"),
    )


def save_graph_structure(compiled_graph: Any, output_path: Path) -> None:
    try:
        mermaid = compiled_graph.get_graph().draw_mermaid()
        content = "# Graph Structure\n\n```mermaid\n" + mermaid + "\n```\n"
    except Exception:
        content = (
            "# Graph Structure\n\n"
            "```mermaid\n"
            "graph TD\n"
            "    START --> start_tool\n"
            "    start_tool --> sql_search_node\n"
            "    sql_search_node --> rerank_retrieve_node\n"
            "    rerank_retrieve_node --> error_router_node\n"
            "    error_router_node -->|ok| final_answer_node\n"
            "    error_router_node -->|error| final_error_node\n"
            "    final_answer_node --> END\n"
            "    final_error_node --> END\n"
            "```\n"
        )
    output_path.write_text(content, encoding="utf-8")


def create_graph():
    load_env()
    llm = build_llm()
    parse_node = create_parse_node(llm=llm)
    sql_search_node = create_sql_search_node()
    rerank_node = create_rerank_node()
    builder = StateGraph(AgentState)
    builder.add_node("start_tool", parse_node)
    builder.add_node("sql_search_node", sql_search_node)
    builder.add_node("rerank_retrieve_node", rerank_node)
    builder.add_node("error_router_node", error_router_node)
    builder.add_node("final_answer_node", final_answer_node)
    builder.add_node("final_error_node", final_error_node)
    builder.add_edge(START, "start_tool")
    builder.add_edge("start_tool", "sql_search_node")
    builder.add_edge("sql_search_node", "error_router_node")
    builder.add_conditional_edges(
        "error_router_node",
        route_by_error,
        {
            "sql_search_node": "sql_search_node",
            "rerank_retrieve_node": "rerank_retrieve_node",
            "final_error_node": "final_error_node",
        },
    )
    builder.add_edge("rerank_retrieve_node", "final_answer_node")
    builder.add_edge("final_answer_node", END)
    builder.add_edge("final_error_node", END)
    return builder.compile()


def run_graph_self_test() -> None:
    def fake_parse_node(state, config, store):
        del state, config, store
        return {"meta_list": [], "event_list": ["进入"], "tool_error": None, "sql_result": [], "rerank_result": [], "retry_count": 0}

    def fake_sql_node(state, config, store):
        del state, config, store
        return {
            "sql_result": [
                {
                    "event_id": 1,
                    "video_id": "demo.mp4",
                    "start_time": 10,
                    "end_time": 20,
                    "_distance": 0.2,
                    "event_summary_cn": "红色目标进入画面",
                }
            ],
            "tool_error": None,
        }

    def fake_rerank_node(state, config, store):
        del config, store
        return {"rerank_result": state.get("sql_result", []), "thought": "ok"}

    builder = StateGraph(AgentState)
    builder.add_node("start_tool", fake_parse_node)
    builder.add_node("sql_search_node", fake_sql_node)
    builder.add_node("rerank_retrieve_node", fake_rerank_node)
    builder.add_node("error_router_node", error_router_node)
    builder.add_node("final_answer_node", final_answer_node)
    builder.add_node("final_error_node", final_error_node)
    builder.add_edge(START, "start_tool")
    builder.add_edge("start_tool", "sql_search_node")
    builder.add_edge("sql_search_node", "error_router_node")
    builder.add_conditional_edges(
        "error_router_node",
        route_by_error,
        {
            "sql_search_node": "sql_search_node",
            "rerank_retrieve_node": "rerank_retrieve_node",
            "final_error_node": "final_error_node",
        },
    )
    builder.add_edge("rerank_retrieve_node", "final_answer_node")
    builder.add_edge("final_answer_node", END)
    builder.add_edge("final_error_node", END)
    graph = builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())
    config = {"configurable": {"thread_id": "self-test", "user_id": "tester"}}
    list(graph.stream({"messages": [HumanMessage(content="test")]}, config, stream_mode="values"))
    final_state = graph.get_state(config)
    assert "final_answer" in final_state.values
    print("graph_self_test_passed")


graph = create_graph()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_graph_self_test()
        raise SystemExit(0)
    save_graph_structure(graph, Path(__file__).resolve().parent / "graph_structure.md")
    config = {"configurable": {"thread_id": "1", "user_id": "Lance"}}
    input_messages = [HumanMessage(content="车进入镜头")]
    for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
    final_state = graph.get_state(config)
