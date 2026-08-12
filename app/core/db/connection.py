import sqlite3
import contextlib

DB_NAME = "hims.db"

@contextlib.contextmanager
def get_db_connection(db_path=DB_NAME):
    """Provides a transactional database connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
