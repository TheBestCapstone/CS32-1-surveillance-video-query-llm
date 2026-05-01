import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage


ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from agents.shared.query_classifier import classify_query  # noqa: E402
from lightingRL.prompt_registry import (  # noqa: E402
    QUERY_CLASSIFICATION_SYSTEM_PROMPT_KEY,
    QUERY_CLASSIFICATION_USER_PROMPT_KEY,
    SELF_QUERY_SYSTEM_PROMPT_KEY,
    SELF_QUERY_USER_PROMPT_KEY,
    SUMMARY_SYSTEM_PROMPT_KEY,
    SUMMARY_USER_PROMPT_KEY,
    get_prompt_template,
    render_prompt,
)
from node.self_query_node import create_self_query_node  # noqa: E402
from node.summary_node import create_summary_node  # noqa: E402


class FakeStructuredOutputModel:
    def __init__(self, recorder, payload):
        self._recorder = recorder
        self._payload = payload

    def invoke(self, messages, config=None):
        del config
        self._recorder.append(messages)
        return self._payload


class FakeStructuredLLM:
    def __init__(self, payload):
        self.calls = []
        self.payload = payload

    def with_structured_output(self, schema):
        del schema
        return FakeStructuredOutputModel(self.calls, self.payload)


class FakeSummaryResponse:
    def __init__(self, content):
        self.content = content


class FakeSummaryLLM:
    def __init__(self, content):
        self.calls = []
        self.content = content
        self.bind_kwargs = {}

    def bind(self, **kwargs):
        self.bind_kwargs = kwargs
        return self

    def invoke(self, messages, config=None):
        del config
        self.calls.append(messages)
        return FakeSummaryResponse(self.content)


def run_smoke_test() -> dict:
    long_query = (
        "Please analyze whether the player who initiated the half court transition "
        "later interacted with teammates before entering the painted area during the same possession"
    )

    self_query_llm = FakeStructuredLLM(
        {
            "rewritten_query": "half court transition interaction before entering painted area",
            "user_need": "Find the possession segment matching the described interaction.",
            "intent_label": "mixed",
            "retrieval_focus": "semantic",
            "key_constraints": ["half court", "interaction", "painted area"],
            "ambiguities": [],
            "reasoning_summary": "Keep the query concise while preserving the sequence constraint.",
            "confidence": 0.91,
        }
    )
    self_query_node = create_self_query_node(llm=self_query_llm)
    self_query_state = self_query_node(
        {"messages": [HumanMessage(content=long_query)]},
        config={},
        store=None,
    )
    self_query_messages = self_query_llm.calls[0]

    classification_llm = FakeStructuredLLM(
        {
            "label": "mixed",
            "confidence": 0.88,
            "reason": "Requires both filtering and semantic understanding.",
        }
    )
    classification_result = classify_query(long_query, llm=classification_llm, config={})
    classification_messages = classification_llm.calls[0]

    rows = [
        {
            "video_id": "demo_video_01",
            "event_id": "event-1",
            "start_time": 10,
            "end_time": 18,
            "event_summary_en": "A player advances the ball and interacts with a teammate near the lane.",
            "_distance": 0.11,
        }
    ]
    raw_answer = "Retrieval complete. Most relevant results:\n[1] event_id=event-1 | video=demo_video_01 | summary=A player advances the ball."
    summary_llm = FakeSummaryLLM("The player advances the ball and interacts with a teammate before entering the lane.")
    summary_node = create_summary_node(llm=summary_llm)
    summary_state = summary_node(
        {
            "original_user_query": long_query,
            "rewritten_query": self_query_state["rewritten_query"],
            "raw_final_answer": raw_answer,
            "rerank_result": rows,
        },
        config={},
        store=None,
    )
    summary_messages = summary_llm.calls[0]

    expected_summary_prompt = render_prompt(
        SUMMARY_USER_PROMPT_KEY,
        original_query=long_query,
        rewritten_query=self_query_state["rewritten_query"],
        row_count=1,
        top_results=[
            {
                "video_id": "demo_video_01",
                "event_id": "event-1",
                "start_time": 10,
                "end_time": 18,
                "summary": "A player advances the ball and interacts with a teammate near the lane.",
            }
        ],
        raw_answer=raw_answer,
    )

    assert self_query_messages[0].content == get_prompt_template(SELF_QUERY_SYSTEM_PROMPT_KEY)
    assert self_query_messages[1].content == render_prompt(SELF_QUERY_USER_PROMPT_KEY, raw_query=long_query)
    assert self_query_state["rewritten_query"] == "half court transition interaction before entering painted area"

    assert classification_messages[0].content == get_prompt_template(QUERY_CLASSIFICATION_SYSTEM_PROMPT_KEY)
    assert classification_messages[1].content == render_prompt(QUERY_CLASSIFICATION_USER_PROMPT_KEY, query=long_query)
    assert classification_result["label"] == "mixed"

    assert summary_llm.bind_kwargs == {"max_tokens": 120}
    assert summary_messages[0].content == get_prompt_template(SUMMARY_SYSTEM_PROMPT_KEY)
    assert summary_messages[1].content == expected_summary_prompt
    assert "Sources:" in summary_state["final_answer"]

    return {
        "self_query_prompt_ok": True,
        "query_classification_prompt_ok": True,
        "summary_prompt_ok": True,
        "summary_final_answer": summary_state["final_answer"],
        "classification_result": classification_result,
        "self_query_result": self_query_state["self_query_result"],
    }


if __name__ == "__main__":
    print(json.dumps(run_smoke_test(), ensure_ascii=False, indent=2))
