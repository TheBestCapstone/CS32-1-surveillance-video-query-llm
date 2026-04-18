import sqlite3
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from node.types import default_sqlite_db_path

@tool
def inspect_database_schema(table_name: str = "episodic_events") -> str:
    """
    Inspect the schema of a specific table in the SQLite database.
    Returns the column names and their data types.
    """
    db_path = default_sqlite_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        if not columns:
            return f"Table '{table_name}' not found."
            
        schema_info = [f"- {col[1]} ({col[2]})" for col in columns]
        return f"Schema for '{table_name}':\n" + "\n".join(schema_info)
    except Exception as e:
        return f"Failed to inspect schema: {str(e)}"

@tool
def inspect_column_enum_values(column_name: str, table_name: str = "episodic_events") -> str:
    """
    Inspect the distinct values present in a specific column.
    Useful for checking exact terms (e.g., what colors or zones actually exist in the database).
    """
    db_path = default_sqlite_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Get all distinct non-empty values for the column
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL AND {column_name} != ''")
        values = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        if not values:
            return f"Column '{column_name}' has no data or does not exist."
            
        return f"Distinct values for '{column_name}':\n" + ", ".join(values)
    except Exception as e:
        return f"Failed to inspect column values: {str(e)}"

@tool
def execute_dynamic_sql(sql_query: str) -> str:
    """
    Execute a dynamically generated SQL SELECT query and return the results.
    WARNING: Always include video_id and event_summary_en in the SELECT clause. Time queries are NOT supported.
    """
    db_path = default_sqlite_db_path()
    try:
        conn = sqlite3.connect(db_path)
        # Set row factory to sqlite3.Row to return dict-like records
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple defense: only allow SELECT queries
        if not sql_query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries are allowed."
            
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        # Extract columns
        if not rows:
            return "Execution successful, but no results returned (0 records)."
            
        columns = rows[0].keys()
        result_list = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        import json
        result_json = json.dumps(result_list, ensure_ascii=False, indent=2)
        # Prevent massive JSON from overloading context limit and causing infinite loops
        truncation_msg = ""
        if len(result_json) > 10000:
            result_list = result_list[:50]
            result_json = json.dumps(result_list, ensure_ascii=False, indent=2)
            truncation_msg = " (Truncated to 50 records due to size limit)"
        
        return f"Execution successful, returned {len(result_list)} records{truncation_msg}:\n" + result_json
    except Exception as e:
        return f"SQL Execution Failed: {str(e)}"
