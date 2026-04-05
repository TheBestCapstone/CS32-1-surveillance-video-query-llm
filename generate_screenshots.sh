#!/bin/bash 
 
echo -e "\n==================================================" 
echo "Week 2-3 Evidence 1: Code snippet of StateGraph construction and node definition in agent/graph.py" 
echo "==================================================" 
cat -n agent/graph.py | sed -n '43,73p' 
 
echo -e "\n==================================================" 
echo "Week 2-3 Evidence 2: Mermaid workflow state machine diagram generated in agent/graph_structure.md" 
echo "==================================================" 
cat agent/graph_structure.md 
 
echo -e "\n==================================================" 
echo "Week 4 Evidence 1: Core code for dynamically generating WHERE clauses in agent/node/pure_sql_node.py" 
echo "==================================================" 
cat -n agent/node/pure_sql_node.py | sed -n '18,48p' 
 
echo -e "\n==================================================" 
echo "Week 4 Evidence 2: Test logs showing successful SQL query construction and execution" 
echo "==================================================" 
# 运行 SQL 相关的测试，模拟 SQL 构建执行过程 
PYTHONPATH=agent python3 -m unittest agent.test.test_sql -v 
 
echo -e "\n==================================================" 
echo "Week 5 Evidence 1: Implementation of _extract_quadruple_with_llm method in agent/node/tool_router_node.py" 
echo "==================================================" 
cat -n agent/node/tool_router_node.py | sed -n '123,150p' 
 
echo -e "\n==================================================" 
echo "Week 5 Evidence 2: Terminal log showing successful routing and Quadruple parsing" 
echo "==================================================" 
# 运行 router 路由测试，展示 LLM 解析后的路由分发结果 
PYTHONPATH=agent python3 -m unittest agent.test.test_router -v 
 
echo -e "\n==================================================" 
echo "Week 6 Evidence 1: Definition of QualityScore and RootCauseAnalysis in agent/node/reflection_node.py" 
echo "==================================================" 
cat -n agent/node/reflection_node.py | sed -n '44,60p' 
 
echo -e "\n==================================================" 
echo "Week 6 Evidence 2: Test run coverage report (test_tool_router_refactor.cover)" 
echo "==================================================" 
cat agent/test_tool_router_refactor.cover