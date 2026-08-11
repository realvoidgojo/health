import sys
import sqlite3
import hashlib
import contextlib
import string
import re
import getpass

DB_NAME = "hims.db"

# ANSI Color Helpers
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}{msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}ERROR: {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}WARNING: {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.CYAN}{msg}{Colors.RESET}")

# Security & Sanitization
def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validates email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_date(date_str: str) -> bool:
    """Validates date string format YYYY-MM-DD."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def sanitize_input(value, cast_type=str, allow_empty=False):
    """Sanitizes input by stripping whitespaces and control characters, and casting to type."""
    if value is None:
        if allow_empty:
            return None
        raise ValueError("Input cannot be empty.")
        
    value = str(value).strip()
    
    # Remove control characters using regex
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    if not value and not allow_empty:
        raise ValueError("Input cannot be empty.")
        
    if not value and allow_empty:
        return None
        
    try:
        if cast_type == int:
            return int(value)
        elif cast_type == float:
            return float(value)
        else:
            return value
    except ValueError:
        raise ValueError(f"Invalid input type. Expected {cast_type.__name__}.")

def getpass_asterisk(prompt="Password: "):
    """Reads password character-by-character and echoes '*' for visual feedback."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    password = []
    try:
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    break
                elif ch in ('\x08', '\x7f'):  # Backspace
                    if password:
                        password.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == '\x03':  # Ctrl+C
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                else:
                    password.append(ch)
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Fallback if termios is not supported or non-interactive
        return getpass.getpass(prompt)
        
    return "".join(password)

def get_input(prompt, cast_type=str, allow_empty=False, is_password=False):
    """Helper to get and sanitize input from the user."""
    while True:
        try:
            # Check if input is mocked (e.g. in unit tests) or sys.stdin is not a tty
            is_mocked = type(input).__name__ != 'builtin_function_or_method' or not sys.stdin.isatty()
            if is_password and not is_mocked:
                try:
                    val = getpass_asterisk(prompt)
                except Exception:
                    val = input(prompt)
            else:
                val = input(prompt)
            return sanitize_input(val, cast_type, allow_empty)
        except ValueError as e:
            print_error(str(e))

# Data Access Layer
@contextlib.contextmanager
def get_db_connection(db_path=DB_NAME):
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Enforce foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(sql, params=(), db_path=DB_NAME):
    """Executes a query (INSERT, UPDATE, DELETE) and returns rowcount or lastrowid."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if sql.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        return cursor.rowcount

def fetch_all(sql, params=(), db_path=DB_NAME):
    """Fetches all rows for a given query."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def fetch_one(sql, params=(), db_path=DB_NAME):
    """Fetches a single row for a given query."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()
