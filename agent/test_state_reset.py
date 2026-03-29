import unittest
from langchain_core.messages import HumanMessage, AIMessage
from node.types import StateResetter, AgentState

class TestStateResetter(unittest.TestCase):
    def test_is_new_query_true(self):
        # 模拟上一轮的 query 是"红色车辆"
        state = {
            "user_query": "红色车辆",
            "messages": [
                HumanMessage(content="红色车辆"),
                AIMessage(content="好的"),
                HumanMessage(content="新查询: 黑色轿车") # 用户输入了新问题
            ]
        }
        self.assertTrue(StateResetter.is_new_query(state))

    def test_is_new_query_false_same_query(self):
        # 用户没有输入新问题，或者输入完全一样
        state = {
            "user_query": "红色车辆",
            "messages": [
                HumanMessage(content="红色车辆")
            ]
        }
        self.assertFalse(StateResetter.is_new_query(state))

    def test_force_reset(self):
        # 强制重置标志
        state = {
            "user_query": "红色车辆",
            "messages": [HumanMessage(content="红色车辆")],
            "force_reset": True
        }
        self.assertTrue(StateResetter.is_new_query(state))

    def test_reset_ephemeral_state(self):
        state = {
            "user_query": "旧查询",
            "tool_choice": {"mode": "sql"},
            "retry_count": 3,
            "hybrid_result": [{"id": 1}],
            "force_reset": True
        }
        
        new_query = "新查询"
        updates = StateResetter.reset_ephemeral_state(state, new_query)
        
        # 验证 user_query 被更新
        self.assertEqual(updates["user_query"], new_query)
        # 验证临时状态被清理
        self.assertEqual(updates["tool_choice"], {})
        self.assertEqual(updates["retry_count"], 0)
        self.assertEqual(updates["hybrid_result"], [])
        self.assertEqual(updates["force_reset"], False)
        # 验证包含其他默认重置字段
        self.assertIn("meta_list", updates)
        self.assertEqual(updates["meta_list"], [])

if __name__ == "__main__":
    unittest.main()