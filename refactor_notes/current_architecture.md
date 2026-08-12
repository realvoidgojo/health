# Current Architecture Analysis

## 1. Overview
The current HIMS application is a procedural, monolithic console application driven by a single entry point in `main.py`. It utilizes a tightly coupled architecture where UI rendering, business logic, and database access are intertwined within long, procedural functions.

## 2. Responsibility Map of `main.py`

### Authentication Flows
- `login_user()`: Authenticates users using hashed passwords. Handles soft-deleted state by redirecting to reactivation flow. Sets global `current_user` state.
- `register_user()`: Registers new customers, validates inputs (email, phone, DOB), assigns a random active policy agent, and creates the user.
- `request_reactivation()`: Allows soft-deleted users to insert a `PENDING` request into `reactivation_requests`.

### Customer Flows
- **Profile (`customer_profile_menu`)**: View profile, edit Name/Phone/DOB, and soft-delete account (`is_deleted=1`, `is_active=0`).
- **Policy (`customer_policy_menu`)**: 
  - Purchase (inserts `PENDING_APPROVAL` into `customer_policies`).
  - View My Policies.
  - View Suggested Policies (computes age, filters master policies).
  - Update Nominee (only for `ACTIVE` policies).
  - Renew (adds 1 year to expiry, sets to `ACTIVE`, only for `EXPIRED`).
  - Cancel (sets to `CANCELLED`, only for `ACTIVE`).
- **Claim (`customer_claim_menu`)**:
  - File Claim (checks if policy is `ACTIVE` and claim amount <= sum insured. Sets `PENDING_ASSIGNMENT`).
  - View Claims.
  - Update Details (only if status is `NEEDS_UPDATE`).

### Agent Flows
- **Dashboard (`agent_dashboard`)**: 
  - Review Pending Policies: View `PENDING_APPROVAL` policies assigned to them.
  - Approve sets status to `ACTIVE` and sets start/expiry dates.
  - Reject sets status to `REJECTED` and allows suggesting an alternative `master_policy`.

### Officer Flows
- **Dashboard (`officer_dashboard`)**:
  - Review Assigned Claims: View claims in `UNDER_REVIEW` or `NEEDS_UPDATE` assigned to them.
  - Mark as `APPROVED`, `REJECTED`, or `NEEDS_UPDATE` (requests info from customer).
  - Records all transitions in `claim_history`.

### Admin Flows
- **User Management**: Search users, process reactivation requests (`APPROVED` sets `is_deleted=0`, `is_active=1`).
- **Agent Management**: Add staff (Agent/Officer), view staff, toggle active status, update phone.
- **Claim Management**: View unassigned pool (`PENDING_ASSIGNMENT`), assign to officer (changes to `UNDER_REVIEW`), view all, search by ID.
- **Policy Management**: View available, search customer policies.
- **Reports**: Aggregate active policies, approved claims, expired policies, rejected claims.

### View Helpers
- `format_inr`, `display_header`, `print_card`, list helpers (`print_my_policies`, etc.) are heavily mixed with DB calls (e.g. `print_available_policies` fetches data AND prints).

### Global State
- `current_user` is a global dictionary populated on login and accessed directly by almost all menu functions, creating severe tight coupling and making unit testing difficult without mocks.

### DB Access
- Raw SQL strings with `execute_query`, `fetch_one`, and `fetch_all` are embedded deeply inside UI while-loops.
