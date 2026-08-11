import os
import sqlite3
import re
from database import DB_NAME, print_success, print_error, print_info, hash_password, get_db_connection

def parse_sql_from_markdown(md_file_path):
    """Parses SQL blocks from a markdown file."""
    if not os.path.exists(md_file_path):
        raise FileNotFoundError(f"Markdown file {md_file_path} not found.")
        
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract all sql blocks
    sql_blocks = re.findall(r'```sql(.*?)```', content, re.DOTALL)
    
    if not sql_blocks:
        raise ValueError("No SQL blocks found in the markdown file.")
        
    # Combine all blocks
    return "\n".join(sql_blocks)

def reset_database():
    """Removes the existing database file if it exists."""
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print_info(f"Existing database '{DB_NAME}' removed successfully.")
        except Exception as e:
            print_error(f"Failed to remove existing database: {e}")
            raise

def init_db():
    """Initializes the database by parsing schema.md and executing the SQL."""
    reset_database()
    
    schema_path = "schema.md"
    try:
        sql_script = parse_sql_from_markdown(schema_path)
    except Exception as e:
        print_error(f"Error parsing {schema_path}: {e}")
        return
        
    # Replace plain text password with hashed password in seed data
    # Find the admin123 string and replace it with its hash
    hashed_admin_pw = hash_password("admin123")
    sql_script = sql_script.replace("'admin123'", f"'{hashed_admin_pw}'")
    
    try:
        # We need a raw sqlite3 connection to execute multiple script statements
        conn = sqlite3.connect(DB_NAME)
        conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print_success(f"Database '{DB_NAME}' created and seeded successfully!")
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
