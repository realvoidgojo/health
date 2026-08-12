import os
import sqlite3
from database import DB_NAME, print_success, print_error, print_info, hash_password, get_db_connection

# Hardcoded SQL Schema and Initial Seed Data
SCHEMA_SQL = """
-- Enable Foreign Key constraints in SQLite
PRAGMA foreign_keys = ON;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('CUSTOMER', 'POLICY_AGENT', 'CLAIM_OFFICER', 'ADMIN')),
    assigned_agent_id INTEGER,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    is_deleted INTEGER DEFAULT 0 CHECK(is_deleted IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_agent_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 2. REACTIVATION REQUESTS TABLE
CREATE TABLE IF NOT EXISTS reactivation_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
    admin_remarks TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. MASTER POLICIES TABLE
CREATE TABLE IF NOT EXISTS master_policies (
    policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Individual Plan', 'Family Floater Plan', 'Senior Citizen Plan')),
    sum_insured REAL NOT NULL,
    premium_amount REAL NOT NULL,
    coverage_details TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
);

-- 4. CUSTOMER POLICIES TABLE
CREATE TABLE IF NOT EXISTS customer_policies (
    customer_policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    policy_id INTEGER NOT NULL,
    nominee_name TEXT NOT NULL,
    nominee_relation TEXT NOT NULL,
    start_date TEXT,
    expiry_date TEXT,
    status TEXT DEFAULT 'PENDING_APPROVAL' CHECK(status IN ('PENDING_APPROVAL', 'ACTIVE', 'EXPIRED', 'CANCELLED', 'REJECTED')),
    assigned_agent_id INTEGER,
    suggested_policy_id INTEGER,
    agent_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (policy_id) REFERENCES master_policies(policy_id),
    FOREIGN KEY (assigned_agent_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (suggested_policy_id) REFERENCES master_policies(policy_id)
);

-- 5. CLAIMS TABLE
CREATE TABLE IF NOT EXISTS claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_policy_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    claim_amount REAL NOT NULL,
    claim_reason TEXT NOT NULL,
    additional_details TEXT,
    status TEXT DEFAULT 'PENDING_ASSIGNMENT' CHECK(status IN ('PENDING_ASSIGNMENT', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'NEEDS_UPDATE')),
    claim_officer_id INTEGER,
    officer_remarks TEXT,
    filed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_policy_id) REFERENCES customer_policies(customer_policy_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (claim_officer_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 6. CLAIM HISTORY TABLE
CREATE TABLE IF NOT EXISTS claim_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    officer_id INTEGER NOT NULL,
    action_taken TEXT NOT NULL CHECK(action_taken IN ('ASSIGNED', 'APPROVED', 'REJECTED', 'REQUESTED_UPDATE', 'CUSTOMER_UPDATED')),
    remarks TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (officer_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- INDEXES FOR PERFORMANCE OPTIMIZATION
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_customer_policies_customer ON customer_policies(customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_customer ON claims(customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_officer ON claims(claim_officer_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);

-- Default Admin Account
INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted)
VALUES ('System Admin', 'admin@hims.com', '{admin_pw_placeholder}', '9999999999', '1985-01-01', 'ADMIN', 1, 0);

-- Master Health Insurance Catalog
INSERT INTO master_policies (policy_name, category, sum_insured, premium_amount, coverage_details) VALUES
('Standard Individual Health Plan', 'Individual Plan', 500000.00, 7200.00, 'In-patient hospitalization, pre & post hospitalization (30/60 days), daycare procedures, ambulance cover.'),
('Comprehensive Family Floater Plan', 'Family Floater Plan', 1000000.00, 18000.00, 'Coverage for spouse and up to 2 children. Cashless treatment across 5000+ hospitals, maternity benefit.'),
('Senior Citizen Healthcare Shield', 'Senior Citizen Plan', 500000.00, 24000.00, 'Tailored for ages 60+. Pre-existing disease cover after 1 year, domiciliary hospitalization, annual free health checkup.');
"""

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
    """Initializes the database by building schema and seeding initial data."""
    reset_database()
    
    try:
        sql_script = SCHEMA_SQL
        
        # Replace default admin password with a securely hashed version
        hashed_admin_pw = hash_password("admin123")
        sql_script = sql_script.replace("{admin_pw_placeholder}", hashed_admin_pw)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            
        print_success(f"Database '{DB_NAME}' created and seeded successfully!")
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    init_db()
