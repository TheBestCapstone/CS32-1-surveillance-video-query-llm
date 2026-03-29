import unittest
from langchain_core.messages import HumanMessage, AIMessage
from node.types import InputValidator, AgentState

class TestInputValidator(unittest.TestCase):
    def test_extract_from_human_message(self):
        # 验证优先从最新的 HumanMessage 中提取
        state = {
            "user_query": "旧查询: 红色车辆",
            "messages": [
                HumanMessage(content="旧查询: 红色车辆"),
                AIMessage(content="好的，为您搜索"),
                HumanMessage(content="新查询: 黑色轿车离开")
            ]
        }
        query = InputValidator.extract_latest_query(state)
        self.assertEqual(query, "新查询: 黑色轿车离开")

    def test_extract_fallback_to_user_query(self):
        # 验证当 messages 为空时，回退到 user_query 字段
        state = {
            "user_query": "直接查询: 行人横穿",
            "messages": []
        }
        query = InputValidator.extract_latest_query(state)
        self.assertEqual(query, "直接查询: 行人横穿")

    def test_sanitize_length_limit(self):
        # 验证长度限制 (最大500字符)
        long_query = "A" * 600
        state = {"user_query": long_query}
        query = InputValidator.extract_latest_query(state)
        self.assertEqual(len(query), 500)

    def test_sanitize_whitespace(self):
        # 验证前后空格被清除
        state = {"user_query": "   带空格的查询   "}
        query = InputValidator.extract_latest_query(state)
        self.assertEqual(query, "带空格的查询")

    def test_empty_input(self):
        # 验证空输入处理
        state = {}
        query = InputValidator.extract_latest_query(state)
        self.assertEqual(query, "")

if __name__ == "__main__":
    unittest.main()
