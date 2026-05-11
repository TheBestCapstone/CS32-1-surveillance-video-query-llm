# 性能基准测试

**Started**: 2026-05-12T02:23:08.900264  
**Elapsed**: 0.00s  

## Results


| Suite     | Total | Passed | Failed |
| --------- | ----- | ------ | ------ |
| 性能指标      | 4     | 4      | 0      |
| **Total** | **4** | **4**  | **0**  |


## 性能指标

- ✅ **分类 fast-path 延迟**
0.03 ms/query (100 runs)
  - `latency_ms`: 0.030
  - `target_ms`: 1.000
- ✅ **Stage1 Chroma global_entity 搜索**
2 ms/query (10 runs)
  - `latency_ms`: 2.000
  - `target_ms`: 500
- ✅ **Stage2 SQLite 展开**
0 ms/query (10 runs)
  - `latency_ms`: 0.000
  - `target_ms`: 200
- ✅ **三路 RRF 融合**
0.093 ms/run (100 runs, 80 sql + 50 hyb + 10 ge)
  - `latency_ms`: 0.093
  - `target_ms`: 10