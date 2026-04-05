import logging
from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from node.types import AgentState

logger = logging.getLogger(__name__)


class SearchMode(str, Enum):
    DIRECT_SEMANTIC = "direct_semantic"
    SQL_FILTER_SEMANTIC = "sql_filter_semantic"


class PreprocessInput(TypedDict):
    user_query: str
    tool_mode: str
    memory_context: Optional[str]
    config: Optional[RunnableConfig]
    store: Optional[BaseStore]


class PreprocessOutput(TypedDict):
    parsed_question: Dict[str, Any]
    meta_list: List[Dict[str, Any]]
    event_list: List[str]
    normalized_query: str
    tool_mode: str
    search_mode: SearchMode
    sql_filter_applied: bool
    preprocessing_applied: bool
    performance_metrics: Dict[str, float]


class BasePreprocessor:
    def __init__(self, name: str, llm: Any = None):
        self.name = name
        self.llm = llm

    @abstractmethod
    def get_system_prompt(self, memory_context: str) -> str:
        pass

    @abstractmethod
    def get_user_prompt_template(self) -> str:
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        pass

    def preprocess(self, state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        raise NotImplementedError
