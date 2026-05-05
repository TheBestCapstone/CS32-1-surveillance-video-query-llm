# RRF ID 一致性修复：Chroma event_id 回填

> **日期**: 2026-05-04
> **分支**: `cursor/消融实验`
> **触发**: code review 发现 `weighted_rrf_fuse()` 中 SQL/BM25/Chroma 三路的 `event_id` 不是同一套 ID 体系，导致 RRF 核心「奖励双路命中」机制完全失效。

---

## 根因


| 来源        | `event_id` 值                                        | 格式                        |
| --------- | --------------------------------------------------- | ------------------------- |
| SQL 分支    | SQLite `event_id INTEGER PRIMARY KEY AUTOINCREMENT` | 整数（如 `42`）                |
| BM25 分支   | SQLite metadata 中的 `event_id`                       | 整数（如 `42`）                |
| Chroma 分支 | Chroma doc ID `{video_id}_{entity_hint}`            | 字符串（如 `"video001_car_3"`） |


`_row_key()` 用 `f"event_id:{event_id}"` 做去重 key。SQL 和 BM25 都返回整数，可以匹配。但 Chroma 返回的是 Chroma 字符串 doc ID，**永远对不上**。同时 Chroma（默认 child collection）是 **track 级别**（多事件聚合），而 SQL/BM25 是 **event 级别**，粒度也不一致。

**后果**：

1. `overlap_count` 恒为 0
2. `_source_type` 永远不会是 `"fused"`
3. 加权 RRF 退化为**加权秩排序合并**，没有双路命中加分

---

## 修复方案

从数据导入规则入手：在 `chroma_builder.py` 构建 Chroma 索引时，回查 SQLite 拿到真实的 `event_id`，写入 Chroma record 的 metadata。后续查询时 `ChromaGateway.search()` 从 metadata 读取 `event_id`。

```
chroma_builder._build_event_records()
  → 每条 event record:
       SELECT event_id FROM episodic_events
       WHERE video_id=? AND entity_hint=? AND ABS(start_time-?)<0.01 AND ABS(end_time-?)<0.01
  → metadata["event_id"] = 查到的整数

chroma_builder._build_child_records()
  → 每个 child (track) record:
       SELECT event_id FROM episodic_events
       WHERE video_id=? AND entity_hint=? ORDER BY start_time
  → metadata["event_ids"] = [id1, id2, ...]
  → metadata["event_id"] = id1 (proxy)

ChromaGateway.search()
  → "event_id": meta.get("event_id") or ids[idx]   # metadata 优先
```

向后兼容：当 SQLite 不存在时（独立构建 Chroma），`_lookup_event_id` 返回 `None`，metadata 不写 `event_id`，`ChromaGateway.search()` fallback 到 Chroma doc ID。

---

## 改动文件

### 1. `agent/db/chroma_builder.py`

- `ChromaBuildConfig` 新增 `sqlite_db_path: Path | None = None`
- `ChromaIndexBuilder.__init__` 存储 `self.sqlite_db_path`
- 新增 `_lookup_event_id(video_id, entity_hint, start_time, end_time) -> int | None`
- 新增 `_lookup_event_ids_for_track(video_id, entity_hint) -> list[int]`
- `_build_event_records()`：metadata 加 `"event_id"` 字段
- `_build_child_records()`：metadata 加 `"event_ids"` + `"event_id"` 字段

### 2. `agent/tools/db_access.py`

- `ChromaGateway.search()`：`"event_id": meta.get("event_id") or ids[idx]`

### 3. `agent/tools/llamaindex_adapter.py`

- 无需改动：原本已使用 `metadata.get("event_id")`（`_build_li_metadata_filters` 路径）

### 4. `agent/test/test_chroma_event_id_backfill.py`（新增）

- 6 个单测：
  - `test_lookup_event_id_by_natural_key`：通过 `(video_id, entity_hint, start_time, end_time)` 查 SQLite 得到正确 `event_id`
  - `test_lookup_event_ids_for_track`：查 track 的全部 `event_id` 列表
  - `test_lookup_without_sqlite_returns_none`：无 SQLite 时返回 None，向后兼容
  - `test_overlap_with_matching_event_ids`：两路 `event_id` 相同时 `overlap_count=1`、`_source_type="fused"`
  - `test_overlap_only_for_same_event_id`：不同 `event_id` 不融合
  - `test_partial_overlap_with_mixed_ids`：混合场景只有匹配的才融合

---

## 测试结果

```
agent/test/test_chroma_event_id_backfill.py  ........  6 passed
agent/test/test_weighted_rrf_fuse.py         .          1 passed
agent/test/test_bm25_index.py                .......... 10 passed
─────────────────────────────────────────────────────────
Total: 17 passed, 0 failed
```

---

## 待办 / 注意事项

1. **现有 Chroma 数据需重建**才能享受此修复。旧数据 metadata 没有 `event_id`，会自动 fallback 到 Chroma doc ID（行为不变）。
2. **Child collection 粒度问题**：child record 聚合了多条 event，metadata 里放了 `event_ids` 列表和代理 `event_id`（第一个）。如果某条 SQL event 恰好是 proxy `event_id`，可以匹配上。更精确的匹配需要切换到 event collection（`AGENT_CHROMA_RETRIEVAL_LEVEL=event`）。
3. **time epsilon**：`_lookup_event_id` 用 `ABS(time - ?) < 0.01` 做浮点数对齐。当 `start_time` 或 `end_time` 为 `None` 时不参与匹配。

