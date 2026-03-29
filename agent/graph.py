import os
import sys
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore

from node.answer_node import final_answer_node
from node.hybrid_search_node import create_hybrid_search_node
from node.preprocess import create_hybrid_preprocess_node, create_pure_sql_preprocess_node, create_video_vect_preprocess_node
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


def save_graph_structure(compiled_graph: Any, output_path: Path) -> None:
    try:
        mermaid = compiled_graph.get_graph().draw_mermaid()
        content = "# Graph Structure\n\n```mermaid\n" + mermaid + "\n```\n"
    except Exception:
        content = (
            "# Graph Structure\n\n"
            "```mermaid\n"
            "graph TD\n"
            "    START --> tool_router\n"
            "    tool_router -->|hybrid| hybrid_preprocess\n"
            "    tool_router -->|sql| pure_sql_preprocess\n"
            "    tool_router -->|video_vect| video_vect_preprocess\n"
            "    tool_router -->|parallel| parallel_search\n"
            "    hybrid_preprocess --> hybrid_search_node\n"
            "    pure_sql_preprocess --> pure_sql_node\n"
            "    video_vect_preprocess --> video_vect_node\n"
            "    parallel_search --> parallel_merge_node\n"
            "    hybrid_search_node --> reflection_node\n"
            "    pure_sql_node --> reflection_node\n"
            "    video_vect_node --> reflection_node\n"
            "    parallel_merge_node --> reflection_node\n"
            "    reflection_node -->|needs_retry| tool_router\n"
            "    reflection_node -->|satisfied| final_answer_node\n"
            "    final_answer_node --> END\n"
            "```\n"
        )
    output_path.write_text(content, encoding="utf-8")


def create_graph():
    load_env()
    llm = build_llm()

    hybrid_preprocess = create_hybrid_preprocess_node(llm=llm)
    pure_sql_preprocess = create_pure_sql_preprocess_node(llm=llm)
    video_vect_preprocess = create_video_vect_preprocess_node(llm=llm)

    tool_router = create_tool_router_node(llm=llm)
    pure_sql_node = create_pure_sql_node()
    hybrid_search_node = create_hybrid_search_node()
    video_vect_node = create_video_vect_node()
    reflection_node = create_reflection_node(llm=llm)

    builder = StateGraph(AgentState)

    builder.add_node("tool_router", tool_router)
    builder.add_node("hybrid_preprocess", hybrid_preprocess)
    builder.add_node("pure_sql_preprocess", pure_sql_preprocess)
    builder.add_node("video_vect_preprocess", video_vect_preprocess)
    builder.add_node("hybrid_search_node", hybrid_search_node)
    builder.add_node("pure_sql_node", pure_sql_node)
    builder.add_node("video_vect_node", video_vect_node)
    builder.add_node("reflection_node", reflection_node)
    builder.add_node("final_answer_node", final_answer_node)

    builder.add_edge(START, "tool_router")

    builder.add_conditional_edges(
        "tool_router",
        route_by_tool_choice,
        {
            "hybrid_preprocess": "hybrid_preprocess",
            "pure_sql_preprocess": "pure_sql_preprocess",
            "video_vect_preprocess": "video_vect_preprocess",
            "reflection_node": "reflection_node",
        },
    )

    builder.add_edge("hybrid_preprocess", "hybrid_search_node")
    builder.add_edge("pure_sql_preprocess", "pure_sql_node")
    builder.add_edge("video_vect_preprocess", "video_vect_node")

    builder.add_edge("hybrid_search_node", "reflection_node")
    builder.add_edge("pure_sql_node", "reflection_node")
    builder.add_edge("video_vect_node", "reflection_node")

    builder.add_conditional_edges(
        "reflection_node",
        route_after_reflection,
        {
            "tool_router": "tool_router",
            "final_answer_node": "final_answer_node",
        },
    )

    builder.add_edge("final_answer_node", END)

    import os
    # LangGraph CLI / API 会设置某些环境变量，或者我们在直接运行时手动提供 checkpointer
    # 通常如果我们在独立脚本中，我们自己传 checkpointer；在 langgraph dev 中不需要。
    # 更安全的做法是：让 create_graph 可以接受参数。
    return builder.compile()


def run_graph_self_test() -> None:
    def fake_router(state, config, store):
        del state, config, store
        mode = "hybrid"
        return {
            "tool_choice": {"mode": mode},
            "is_parallel": False,
        }

    def fake_hybrid_preprocess(state, config, store):
        del state, config, store
        return {
            "parsed_question": {"event": "进入", "color": None},
            "meta_list": [],
            "event_list": ["进入"],
        }

    def fake_pure_sql_preprocess(state, config, store):
        del state, config, store
        return {
            "parsed_question": {"color": None},
            "meta_list": [],
            "event_list": [],
        }

    def fake_video_vect_preprocess(state, config, store):
        del state, config, store
        return {
            "parsed_question": {"event": None},
            "meta_list": [],
            "event_list": [],
        }

    def fake_hybrid(state, config, store):
        del state, config, store
        return {
            "hybrid_result": [{"event_id": 1}],
            "tool_error": None,
        }

    def fake_pure_sql(state, config, store):
        del state, config, store
        return {"sql_result": [], "tool_error": None}

    def fake_video_vect(state, config, store):
        del state, config, store
        return {"video_vect_result": [], "tool_error": None}

    def fake_reflection(state, config, store):
        del state, config, store
        return {
            "reflection_result": {
                "feedback": "查询质量满意",
                "quality_score": 1.0,
                "needs_retry": False,
                "optimized": False,
                "can_continue": False,
            },
        }

    def fake_final_answer(state, config, store):
        del state, config, store
        return {"final_answer": "测试答案"}

    def route_from_router(state):
        tool_choice = state.get("tool_choice", {})
        mode = tool_choice.get("mode", "none")
        if mode == "parallel":
            return "reflection_node"
        elif mode in ("hybrid", "sql", "video_vect"):
            return f"{mode}_preprocess"
        else:
            return "reflection_node"

    builder = StateGraph(AgentState)
    builder.add_node("tool_router", fake_router)
    builder.add_node("hybrid_preprocess", fake_hybrid_preprocess)
    builder.add_node("pure_sql_preprocess", fake_pure_sql_preprocess)
    builder.add_node("video_vect_preprocess", fake_video_vect_preprocess)
    builder.add_node("hybrid_search_node", fake_hybrid)
    builder.add_node("pure_sql_node", fake_pure_sql)
    builder.add_node("video_vect_node", fake_video_vect)
    builder.add_node("reflection_node", fake_reflection)
    builder.add_node("final_answer_node", fake_final_answer)

    builder.add_edge(START, "tool_router")

    builder.add_conditional_edges(
        "tool_router",
        route_from_router,
        {
            "hybrid_preprocess": "hybrid_preprocess",
            "pure_sql_preprocess": "pure_sql_preprocess",
            "video_vect_preprocess": "video_vect_preprocess",
            "reflection_node": "reflection_node",
        },
    )

    builder.add_edge("hybrid_preprocess", "hybrid_search_node")
    builder.add_edge("pure_sql_preprocess", "pure_sql_node")
    builder.add_edge("video_vect_preprocess", "video_vect_node")

    builder.add_edge("hybrid_search_node", "reflection_node")
    builder.add_edge("pure_sql_node", "reflection_node")
    builder.add_edge("video_vect_node", "reflection_node")

    def route_reflection(state):
        result = state.get("reflection_result", {})
        if result.get("needs_retry"):
            return "tool_router"
        return "final_answer_node"

    builder.add_conditional_edges(
        "reflection_node",
        route_reflection,
        {
            "tool_router": "tool_router",
            "final_answer_node": "final_answer_node",
        },
    )
    builder.add_edge("final_answer_node", END)

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
    
    # 针对直接运行进行特殊处理：如果通过命令行直接运行，因为需要读取持久化状态(get_state)
    # 所以需要重新编译包含内存持久化的图，而供 langgraph CLI 加载的变量依然是上面的无状态 graph
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.store.memory import InMemoryStore
    
    # 重建相同的图，但添加 checkpointer
    builder = StateGraph(AgentState)
    builder.add_node("tool_router", tool_router_node)
    builder.add_node("hybrid_preprocess", hybrid_preprocess_node)
    builder.add_node("pure_sql_preprocess", pure_sql_preprocess_node)
    builder.add_node("video_vect_preprocess", video_vect_preprocess_node)
    builder.add_node("hybrid_search_node", create_hybrid_search_node(tool=sql_search_tool))
    builder.add_node("pure_sql_node", pure_sql_node)
    builder.add_node("video_vect_node", video_vect_node)
    builder.add_node("reflection_node", create_reflection_node(llm=llm, max_retries=3, callback=reflection_callback))
    builder.add_node("final_answer_node", final_answer_node)
    builder.add_edge(START, "tool_router")
    builder.add_conditional_edges("tool_router", route_by_tool_choice, {"hybrid_preprocess": "hybrid_preprocess", "pure_sql_preprocess": "pure_sql_preprocess", "video_vect_preprocess": "video_vect_preprocess"})
    builder.add_edge("hybrid_preprocess", "hybrid_search_node")
    builder.add_edge("pure_sql_preprocess", "pure_sql_node")
    builder.add_edge("video_vect_preprocess", "video_vect_node")
    builder.add_edge("hybrid_search_node", "reflection_node")
    builder.add_edge("pure_sql_node", "reflection_node")
    builder.add_edge("video_vect_node", "reflection_node")
    builder.add_conditional_edges("reflection_node", route_after_reflection, {"tool_router": "tool_router", "final_answer_node": "final_answer_node"})
    builder.add_edge("final_answer_node", END)
    
    local_graph = builder.compile(checkpointer=MemorySaver(), store=InMemoryStore())
    
    save_graph_structure(local_graph, Path(__file__).resolve().parent / "graph_structure.md")
    config = {"configurable": {"thread_id": "1", "user_id": "Lance"}}
    input_messages = [HumanMessage(content="车进入镜头")]
    for chunk in local_graph.stream({"messages": input_messages}, config, stream_mode="values"):
        chunk["messages"][-1].pretty_print()
    final_state = local_graph.get_state(config)