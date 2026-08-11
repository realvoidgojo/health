# Database Schema: Health Insurance Management System (HIMS)

This document defines the complete relational database schema for the HIMS console application using **SQLite3**. 

---

## 1. Entity Relationship Overview

```
       ┌──────────────────────┐
       │        USERS         │
       │ (Customer/Agent/     │
       │  Officer/Admin)      │
       └──────────┬───────────┘
                  │
        ┌─────────┼──────────────────────────────┐
        │ 1:N     │ 1:N                          │ 1:N
        ▼         ▼                              ▼
┌──────────────┐ ┌──────────────────────┐ ┌────────────────────────┐
│ REACTIVATION │ │  CUSTOMER_POLICIES   │ │        CLAIMS          │
│   REQUESTS   │ │ (Purchased Policies) │ │ (Filed Claims Pool)    │
└──────────────┘ └──────────┬───────────┘ └──────────┬─────────────┘
                            │                        │
                        N:1 │                    1:N │
                            ▼                        ▼
                 ┌──────────────────────┐ ┌────────────────────────┐
                 │   MASTER_POLICIES    │ │     CLAIM_HISTORY      │
                 │   (Policy Catalog)   │ │     (Audit Log)        │
                 └──────────────────────┘ └────────────────────────┘
```

---

## 2. Data Dictionary

### 2.1 `users`
Stores credentials, personal details, roles, and status flags for all entities in the system.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier for each user |
| `full_name` | TEXT | NOT NULL | User's full name |
| `email` | TEXT | UNIQUE, NOT NULL | User's login email address |
| `password` | TEXT | NOT NULL | User's account password |
| `phone` | TEXT | NOT NULL | Contact telephone number |
| `date_of_birth` | TEXT | NOT NULL | Date of birth (YYYY-MM-DD) |
| `role` | TEXT | NOT NULL, CHECK | Role: `'CUSTOMER'`, `'POLICY_AGENT'`, `'CLAIM_OFFICER'`, `'ADMIN'` |
| `assigned_agent_id` | INTEGER | FOREIGN KEY (`users.user_id`) | ID of assigned Policy Agent (for Customers) |
| `is_active` | INTEGER | DEFAULT 1, CHECK(0 or 1) | `1` = Active, `0` = Deactivated |
| `is_deleted` | INTEGER | DEFAULT 0, CHECK(0 or 1) | `1` = Soft Deleted, `0` = Existing |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

### 2.2 `reactivation_requests`
Tracks requests raised by soft-deleted customers to reactivate their accounts.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `request_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique request identifier |
| `user_id` | INTEGER | FOREIGN KEY (`users.user_id`) | ID of customer requesting reactivation |
| `request_date` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when request was submitted |
| `status` | TEXT | DEFAULT 'PENDING', CHECK | Status: `'PENDING'`, `'APPROVED'`, `'REJECTED'` |
| `admin_remarks` | TEXT | NULLABLE | Notes added by Admin upon review |

### 2.3 `master_policies`
Catalog of health insurance plans offered by the provider.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `policy_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique master policy ID |
| `policy_name` | TEXT | NOT NULL | Name of the plan |
| `category` | TEXT | NOT NULL, CHECK | Category: `'Individual Plan'`, `'Family Floater Plan'`, `'Senior Citizen Plan'` |
| `sum_insured` | REAL | NOT NULL | Total financial coverage limit |
| `premium_amount` | REAL | NOT NULL | Annual policy premium cost |
| `coverage_details` | TEXT | NOT NULL | Extended breakdown of covered medical risks |
| `is_active` | INTEGER | DEFAULT 1 | Catalog status (`1` = Available, `0` = Archived) |

### 2.4 `customer_policies`
Tracks policy purchases, renewals, status changes, and agent recommendations.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `customer_policy_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique instance ID for customer's policy |
| `customer_id` | INTEGER | FOREIGN KEY (`users.user_id`) | Customer owner ID |
| `policy_id` | INTEGER | FOREIGN KEY (`master_policies.policy_id`) | Purchased master policy reference |
| `nominee_name` | TEXT | NOT NULL | Full name of policy nominee |
| `nominee_relation` | TEXT | NOT NULL | Nominee's relationship to customer |
| `start_date` | TEXT | NULLABLE | Policy start date (YYYY-MM-DD) |
| `expiry_date` | TEXT | NULLABLE | Policy expiry date (YYYY-MM-DD) |
| `status` | TEXT | DEFAULT 'PENDING_APPROVAL', CHECK | Status: `'PENDING_APPROVAL'`, `'ACTIVE'`, `'EXPIRED'`, `'CANCELLED'`, `'REJECTED'` |
| `assigned_agent_id` | INTEGER | FOREIGN KEY (`users.user_id`) | Agent responsible for reviewing/assigning |
| `suggested_policy_id`| INTEGER | FOREIGN KEY (`master_policies.policy_id`) | Alternative policy suggested by agent if rejected |
| `agent_remarks` | TEXT | NULLABLE | Review comments/reasons from agent |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Purchase request timestamp |

### 2.5 `claims`
Manages claims filed by customers against active policies and tracks processing states.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `claim_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique claim reference ID |
| `customer_policy_id` | INTEGER | FOREIGN KEY (`customer_policies.customer_policy_id`) | Policy against which claim is raised |
| `customer_id` | INTEGER | FOREIGN KEY (`users.user_id`) | Customer filing the claim |
| `claim_amount` | REAL | NOT NULL | Monetary amount claimed |
| `claim_reason` | TEXT | NOT NULL | Medical/hospitalization reason |
| `additional_details` | TEXT | NULLABLE | Supplementary data provided by customer upon update request |
| `status` | TEXT | DEFAULT 'PENDING_ASSIGNMENT', CHECK | Status: `'PENDING_ASSIGNMENT'`, `'UNDER_REVIEW'`, `'APPROVED'`, `'REJECTED'`, `'NEEDS_UPDATE'` |
| `claim_officer_id` | INTEGER | FOREIGN KEY (`users.user_id`) | Claim Officer processing the claim |
| `officer_remarks` | TEXT | NULLABLE | Notes or reasons provided by Claim Officer |
| `filed_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Submission timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

### 2.6 `claim_history`
Audit log capturing every evaluation action taken by Claim Officers for reporting and history tracking.

| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `history_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Audit log ID |
| `claim_id` | INTEGER | FOREIGN KEY (`claims.claim_id`) | Associated claim |
| `officer_id` | INTEGER | FOREIGN KEY (`users.user_id`) | Officer executing the action |
| `action_taken` | TEXT | NOT NULL, CHECK | Action: `'ASSIGNED'`, `'APPROVED'`, `'REJECTED'`, `'REQUESTED_UPDATE'`, `'CUSTOMER_UPDATED'` |
| `remarks` | TEXT | NULLABLE | Feedback/notes recorded at action time |
| `action_timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp of action |

---

## 3. SQL DDL Implementation (`schema.sql`)

```sql
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
```

---

## 4. Initial Seed Data (`seed.sql`)

```sql
-- Default Admin Account
INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted)
VALUES ('System Admin', 'admin@hims.com', 'admin123', '9999999999', '1985-01-01', 'ADMIN', 1, 0);

-- Master Health Insurance Catalog
INSERT INTO master_policies (policy_name, category, sum_insured, premium_amount, coverage_details) VALUES
('Standard Individual Health Plan', 'Individual Plan', 500000.00, 12000.00, 'In-patient hospitalization, pre & post hospitalization (30/60 days), daycare procedures, ambulance cover.'),
('Comprehensive Family Floater Plan', 'Family Floater Plan', 1000000.00, 24000.00, 'Coverage for spouse and up to 2 children. Cashless treatment across 5000+ hospitals, maternity benefit.'),
('Senior Citizen Healthcare Shield', 'Senior Citizen Plan', 750000.00, 30000.00, 'Tailored for ages 60+. Pre-existing disease cover after 1 year, domiciliary hospitalization, annual free health checkup.');
```
