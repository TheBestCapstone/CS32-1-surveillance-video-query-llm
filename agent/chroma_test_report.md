# Chroma 测试报告

- collection: `basketball_tracks`
- record_count: `26`
- source_event_count: `27`
- chunking: `track-level aggregation (video_id_entity_hint)`
- embedding: `text-embedding-v3 (1024)`

## 检索策略测试
### Query: 场边站立不动的人 (zh)
- Cosine Top3:
  - basketball_1.mp4_track_24 | dist=0.2702 | zone=sidewalk
  - basketball_1.mp4_track_36 | dist=0.2719 | zone=sidewalk
  - basketball_1.mp4_track_29 | dist=0.2765 | zone=sidewalk
- BM25 Top3:
  - basketball_1.mp4_track_1 | bm25=0.0000 | zone=sidewalk
  - basketball_1.mp4_track_2 | bm25=0.0000 | zone=sidewalk
  - basketball_1.mp4_track_3 | bm25=0.0000 | zone=sidewalk
- Hybrid Top3:
  - basketball_1.mp4_track_24 | score=0.6000 | cos=0.7298 | bm25=0.0000
  - basketball_1.mp4_track_36 | score=0.5796 | cos=0.7281 | bm25=0.0000
  - basketball_1.mp4_track_29 | score=0.5233 | cos=0.7235 | bm25=0.0000

### Query: 快速移动的目标 (zh)
- Cosine Top3:
  - basketball_1.mp4_track_26 | dist=0.4719 | zone=road_right
  - basketball_2.mp4_track_id_2 | dist=0.5040 | zone=court center-right
  - basketball_2.mp4_track_id_4 | dist=0.5045 | zone=court upper-middle
- BM25 Top3:
  - basketball_1.mp4_track_1 | bm25=0.0000 | zone=sidewalk
  - basketball_1.mp4_track_2 | bm25=0.0000 | zone=sidewalk
  - basketball_1.mp4_track_3 | bm25=0.0000 | zone=sidewalk
- Hybrid Top3:
  - basketball_1.mp4_track_26 | score=0.6000 | cos=0.5281 | bm25=0.0000
  - basketball_2.mp4_track_id_2 | score=0.3905 | cos=0.4960 | bm25=0.0000
  - basketball_2.mp4_track_id_4 | score=0.3872 | cos=0.4955 | bm25=0.0000

### Query: person standing still near baseline (en)
- Cosine Top3:
  - basketball_1.mp4_track_11 | dist=0.2101 | zone=sidewalk
  - basketball_1.mp4_track_9 | dist=0.2106 | zone=parking
  - basketball_1.mp4_track_3 | dist=0.2172 | zone=sidewalk
- BM25 Top3:
  - basketball_1.mp4_track_1 | bm25=2.0648 | zone=sidewalk
  - basketball_1.mp4_track_2 | bm25=2.0648 | zone=sidewalk
  - basketball_1.mp4_track_3 | bm25=2.0648 | zone=sidewalk
- Hybrid Top3:
  - basketball_1.mp4_track_11 | score=1.0000 | cos=0.7899 | bm25=2.0648
  - basketball_1.mp4_track_9 | score=0.9979 | cos=0.7894 | bm25=2.0648
  - basketball_1.mp4_track_3 | score=0.9672 | cos=0.7828 | bm25=2.0648

### Query: fast moving target (en)
- Cosine Top3:
  - basketball_1.mp4_track_26 | dist=0.4735 | zone=road_right
  - basketball_2.mp4_track_id_3 | dist=0.4940 | zone=court left-center
  - basketball_2.mp4_track_id_4 | dist=0.4952 | zone=court upper-middle
- BM25 Top3:
  - basketball_2.mp4_track_id_2 | bm25=2.2049 | zone=court center-right
  - basketball_2.mp4_track_id_4 | bm25=1.9432 | zone=court upper-middle
  - basketball_2.mp4_track_id_3 | bm25=1.8868 | zone=court left-center
- Hybrid Top3:
  - basketball_1.mp4_track_26 | score=0.9191 | cos=0.5265 | bm25=1.7591
  - basketball_2.mp4_track_id_2 | score=0.8171 | cos=0.5007 | bm25=2.2049
  - basketball_2.mp4_track_id_4 | score=0.7987 | cos=0.5048 | bm25=1.9432

