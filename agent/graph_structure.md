# Graph Structure

## Default Graph: `parallel_fusion`

```mermaid
graph TD
    START([START]) --> self_query_node
    self_query_node --> query_classification_node
    query_classification_node --> parallel_retrieval_fusion_node
    parallel_retrieval_fusion_node --> final_answer_node
    final_answer_node --> summary_node
    summary_node --> END([END])
```

## Fallback Graph: `legacy_router`

```mermaid
graph TD
    START([START]) --> self_query_node
    self_query_node --> tool_router
    tool_router -->|hybrid_search| hybrid_search_node
    tool_router -->|pure_sql| pure_sql_node
    hybrid_search_node --> reflection_node
    pure_sql_node --> reflection_node
    reflection_node -->|needs_retry| tool_router
    reflection_node -->|ok/stop| final_answer_node
    final_answer_node --> summary_node
    summary_node --> END([END])
```

## Structural Notes

- `self_query_node` is inserted before all retrieval paths.
- `summary_node` is inserted after `final_answer_node`.
- The default path does not perform hard single-route branching.
- The default path always executes dual retrieval and lets fusion absorb label bias.
