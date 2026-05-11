# 融合层三路 RRF 测试

**Started**: 2026-05-12T02:23:04.236287  
**Elapsed**: 0.00s  

## Results


| Suite             | Total | Passed | Failed |
| ----------------- | ----- | ------ | ------ |
| weighted_rrf_fuse | 5     | 5      | 0      |
| **Total**         | **5** | **5**  | **0**  |


## weighted_rrf_fuse

- ✅ **普通模式（无 GE rows）→ 二路 RRF**
weights={'sql': 0.5, 'hybrid': 0.5, 'global_entity': 0.0} fused=2
  - `sql`: 0.500
  - `hybrid`: 0.500
  - `global_entity`: 0.000
- ✅ **多摄像头模式（GE rows）→ 三路 RRF GE=0.65 主导**
weights={'sql': 0.15, 'hybrid': 0.2, 'global_entity': 0.65} fused=4
  - `sql`: 0.150
  - `hybrid`: 0.200
  - `global_entity`: 0.650
- ✅ **GE rows 为空列表 → 退化为普通模式**
weights={'sql': 0.5, 'hybrid': 0.5, 'global_entity': 0.0}
  - `sql`: 0.500
  - `hybrid`: 0.500
  - `global_entity`: 0.000
- ✅ **所有分支为空 → 不报错返回空列表**
fused=0
- ✅ **_row_key 适配 global_entity_id**
event_id:1 | ge:ge1:10.0 | ge:ge1:10.0