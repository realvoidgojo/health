import sys
from database import fetch_all, get_db_connection, print_info, print_error, print_success, get_input, Colors

def get_tables():
    """Fetches all user-created tables from the database."""
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    rows = fetch_all(sql)
    return [row['name'] for row in rows]

def print_table_data(table_name, page=0, page_size=10):
    """Prints a paginated view of a table using a clean ASCII grid."""
    offset = page * page_size
    
    # Get column names
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            if not columns_info:
                print_error(f"Table '{table_name}' does not exist.")
                return 0
            columns = [col['name'] for col in columns_info]
            
            # Get total rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            # Fetch data page
            cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (page_size, offset))
            rows = cursor.fetchall()
            
    except Exception as e:
        print_error(f"Error reading table {table_name}: {e}")
        return 0

    if total_rows == 0:
        print_info(f"Table '{table_name}' is empty.")
        return 0

    # Calculate column widths based on headers and data
    col_widths = {col: len(col) for col in columns}
    for row in rows:
        for i, col in enumerate(columns):
            val_str = str(row[i])
            if len(val_str) > col_widths[col]:
                col_widths[col] = len(val_str)
                
    # Create ASCII grid separators
    separator = "+" + "+".join(["-" * (col_widths[col] + 2) for col in columns]) + "+"
    
    print(f"\n{Colors.CYAN}--- Table: {table_name} (Page {page + 1} of {max(1, (total_rows + page_size - 1) // page_size)}) ---{Colors.RESET}")
    print(separator)
    
    # Print Headers
    header_row = "|" + "|".join([f" {col.ljust(col_widths[col])} " for col in columns]) + "|"
    print(header_row)
    print(separator)
    
    # Print Rows
    for row in rows:
        row_str = "|" + "|".join([f" {str(row[i]).ljust(col_widths[col])} " for i, col in enumerate(columns)]) + "|"
        print(row_str)
    
    print(separator)
    print(f"Showing rows {offset + 1} to min({offset + len(rows)}, {total_rows}) of {total_rows}")
    return total_rows

def view_table(table_name):
    """Interactive pagination for a specific table."""
    page = 0
    page_size = 10
    
    while True:
        total_rows = print_table_data(table_name, page, page_size)
        if total_rows == 0:
            break
            
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        
        print("\nNavigation: [N] Next 10 | [P] Previous 10 | [B] Back to Table List")
        cmd = get_input("Select option: ", cast_type=str).upper()
        
        if cmd == 'N':
            if page < total_pages - 1:
                page += 1
            else:
                print_info("Already on the last page.")
        elif cmd == 'P':
            if page > 0:
                page -= 1
            else:
                print_info("Already on the first page.")
        elif cmd == 'B':
            break
        else:
            print_error("Invalid option. Please choose N, P, or B.")

def main_menu():
    while True:
        print(f"\n{Colors.GREEN}=== DB Viewer Menu ==={Colors.RESET}")
        tables = get_tables()
        
        if not tables:
            print_error("No tables found in the database.")
            break
            
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")
            
        print("0. Exit")
        
        choice = get_input("\nSelect a table number to view: ", cast_type=int)
        
        if choice == 0:
            print_info("Exiting DB Viewer.")
            break
        elif 1 <= choice <= len(tables):
            view_table(tables[choice - 1])
        else:
            print_error("Invalid selection.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print_info("\nExiting DB Viewer.")
        sys.exit(0)
