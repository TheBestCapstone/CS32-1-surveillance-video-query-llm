# Video Event Retrieval Agent

This project implements a multi-agent system for querying video events using both structured metadata (SQLite) and semantic vector search (LanceDB).

## System Architecture
- **Master Router**: Routes queries to appropriate sub-agents based on the presence of location or structured features.
- **Pure SQL Sub-Agent**: Handles metadata-heavy queries autonomously.
- **Hybrid Search Sub-Agent**: Handles location-based and semantic queries autonomously.

## Important Limitations (Explicit Disclaimer)
**⚠️ TIME-DIMENSION QUERIES ARE NOT SUPPORTED**

The current models and database schema have been explicitly designed to **exclude** time-based filtering and sorting logic. 
- You cannot query for events happening at a specific time (e.g., "morning", "14:00", "last 10 seconds").
- You cannot filter events based on duration (e.g., "stationary for a long time").
- You cannot sort events chronologically.

The system will intentionally ignore time-related constraints in natural language prompts to focus purely on objects, colors, locations, and semantic actions.

## Testing
Run the English test suite (20 comprehensive cases covering CRUD, boundary, and exception scenarios) via:
```bash
python agent/test/result_test_runner.py
```
Check `result.md` for the latest detailed test report.
