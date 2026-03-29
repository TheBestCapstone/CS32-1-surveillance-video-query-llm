from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def create_syntax_check_node():
    def syntax_check_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del config, store
        syntax_valid = True
        syntax_error = None

        meta_list = state.get("meta_list", [])
        for item in meta_list:
            if not isinstance(item, dict):
                syntax_valid = False
                syntax_error = f"元数据项格式错误: {item} 不是字典类型"
                break
            field = item.get("field", "")
            op = item.get("op", "")
            value = item.get("value")
            if not field or not op:
                syntax_valid = False
                syntax_error = f"元数据项缺少必要字段: {item}"
                break
            valid_ops = {"==", "=", "!=", "<>", ">", ">=", "<", "<=", "contains"}
            if op.lower() not in valid_ops:
                syntax_valid = False
                syntax_error = f"不支持的操作符: {op}"
                break

        tool_choice = state.get("tool_choice", {})
        if not tool_choice.get("mode"):
            syntax_valid = False
            syntax_error = "工具选择未完成，无法确定检索模式"

        thought = f"语法检查: {'通过' if syntax_valid else '失败'}, 错误: {syntax_error}"
        return {
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "thought": thought,
            "messages": [AIMessage(content=syntax_error or "语法检查通过")],
        }

    return syntax_check_node


def route_after_syntax_check(state: AgentState) -> str:
    if state.get("syntax_valid", False):
        return "rerank_retrieve_node"
    return "final_error_node"


if __name__ == "__main__":
    check = create_syntax_check_node()
    out1 = check({
        "meta_list": [{"field": "object_color_cn", "op": "contains", "value": "红色"}],
        "tool_choice": {"mode": "hybrid"},
    }, {}, None)
    print("valid test:", out1["syntax_valid"])

    out2 = check({
        "meta_list": [{"field": "object_color_cn", "op": "invalid_op", "value": "红色"}],
        "tool_choice": {"mode": "hybrid"},
    }, {}, None)
    print("invalid test:", out2["syntax_valid"], out2["syntax_error"])