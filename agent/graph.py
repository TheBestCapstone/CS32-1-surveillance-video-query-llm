import os
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from node.answer_node import final_answer_node
from node.hybrid_search_node import create_hybrid_search_node
from node.parallel_search_node import create_parallel_search_node
from node.pure_sql_node import create_pure_sql_node
from node.reflection_node import create_reflection_node, route_after_reflection
from node.tool_router_node import create_tool_router_node, route_by_tool_choice
from node.types import AgentState
from node.video_vect_node import create_video_vect_node


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


def create_graph():
    load_env()
    llm = build_llm()

    tool_router = create_tool_router_node(llm=llm)
    hybrid_search_node = create_hybrid_search_node()
    pure_sql_node = create_pure_sql_node()
    video_vect_node = create_video_vect_node()
    parallel_search_node = create_parallel_search_node()
    reflection_node = create_reflection_node(llm=llm)

    builder = StateGraph(AgentState)
    builder.add_node("tool_router", tool_router)
    builder.add_node("hybrid_search_node", hybrid_search_node)
    builder.add_node("pure_sql_node", pure_sql_node)
    builder.add_node("video_vect_node", video_vect_node)
    builder.add_node("parallel_search_node", parallel_search_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("final_answer_node", final_answer_node)

    builder.add_edge(START, "tool_router")
    builder.add_conditional_edges(
        "tool_router",
        route_by_tool_choice,
        {
            "hybrid_search_node": "hybrid_search_node",
            "pure_sql_node": "pure_sql_node",
            "video_vect_node": "video_vect_node",
            "parallel_search_node": "parallel_search_node",
        },
    )
    builder.add_edge("hybrid_search_node", "reflection_node")
    builder.add_edge("pure_sql_node", "reflection_node")
    builder.add_edge("video_vect_node", "reflection_node")
    builder.add_edge("parallel_search_node", "reflection_node")
    builder.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {"tool_router": "tool_router", "final_answer_node": "final_answer_node"},
    )
    builder.add_edge("final_answer_node", END)
    return builder.compile()


graph = create_graph()


if __name__ == "__main__":
    local_graph = create_graph()
    config = {"configurable": {"thread_id": "1", "user_id": "Lance"}}
    for chunk in local_graph.stream({"messages": [HumanMessage(content="车进入镜头")]}, config, stream_mode="values"):
        if chunk.get("messages"):
            chunk["messages"][-1].pretty_print()
    final_state = local_graph.get_state(config)
    print("final_answer:", final_state.values.get("final_answer"))
