from app.core.db.connection import get_db_connection

def execute_query(sql, params=(), db_path="hims.db"):
    """Executes a non-SELECT query and returns the last row ID (or rowcount for updates)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if sql.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        else:
            return cursor.rowcount

def fetch_all(sql, params=(), db_path="hims.db"):
    """Fetches all rows for a SELECT query."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def fetch_one(sql, params=(), db_path="hims.db"):
    """Fetches a single row for a SELECT query."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()
