# Case Study: Health Insurance Management System (HIMS)

## 1. Project Overview
The Health Insurance Management System (HIMS) is a comprehensive console-based application designed to streamline the operations of an insurance provider. It manages the entire lifecycle of health insurance services, bridging the gap between Customers seeking insurance, Policy Agents advising them, Claim Officers processing their requests, and Administrators overseeing the entire ecosystem. 

This system is built entirely using **Python** for the application logic and **SQLite3** for robust, lightweight relational database management.

## 2. Technology Stack
*   **Programming Language:** Python 3.x
*   **Database:** SQLite3 (via the built-in `sqlite3` module)
*   **Interface:** Command Line Interface (CLI) / Console Menu
*   **Architecture:** Python Database Connectivity (PDBC) pattern with distinct roles and menus.

## 3. System Roles
The application defines four distinct user roles, each with strict access controls and tailored dashboards:
1.  **Customer:** The primary end-user who buys and manages policies and files claims.
2.  **Policy Agent:** An intermediate consultant assigned to manage specific customers, reviewing their policy requests, and offering suggestions.
3.  **Claim Officer:** A specialized agent responsible solely for evaluating, approving, rejecting, or requesting more information on customer claims.
4.  **Admin:** The system supervisor handling user/agent onboarding, claim assignments, global searches, and report generation.

## 4. Policy Categories
The system offers specialized health insurance plans tailored to different demographic needs:

| Category | Description |
| :--- | :--- |
| **Individual Plan** | Covers a single person under the policy sum insured. |
| **Family Floater Plan** | Covers the entire family under one shared coverage amount. |
| **Senior Citizen Plan** | Specially designed health coverage for individuals aged 60 and above. |

---

## 5. Functional Requirements & User Stories

### A. Customer Module
**Profile Management:**
*   **Register & Login:** Customers must be able to create an account and authenticate securely.
*   **Manage Details:** Customers can view and update their profile details at any time.
*   **Account Lifecycle:** Customers can perform a "Soft Delete" on their account to deactivate it, and subsequently raise a "Reactivation Request" if they wish to return.

**Policy Management:**
*   **Explore:** Customers can view a master catalog of available policies (including coverage details) and receive automated or agent-driven suggested policies.
*   **Transact:** Customers can purchase new policies.
*   **Maintain:** Customers can view all their active/expired policies, update nominee information, renew expiring policies, and cancel active policies.

**Claim Management:**
*   **File Claims:** Customers can file a claim against an active policy.
*   **Track Status:** Customers can view all their submitted claims and check their current status (Pending, Approved, Rejected, Needs Update).
*   **Update Claims:** If a Claim Officer flags a claim for insufficient details, the customer must be able to update and resubmit the claim.

### B. Policy Agent Module
**Customer Management:**
*   **Dashboard:** Agents log in and view a list of customers assigned to them by the system.
*   **Oversight:** Agents can view the current policies held by their assigned customers.
*   **Advisory Action:** Agents review customer requests to purchase a policy. They can officially "Assign" (approve) the policy to the customer, or "Reject" the request and suggest alternative policies better suited to the customer's profile.

### C. Claim Officer Module
**Claim Management:**
*   **Work Queue:** Officers log in and view their assigned claims from the global pool.
*   **Review Process:** Officers evaluate claims and make one of three decisions:
    1.  *Approve* the claim.
    2.  *Reject* the claim (with reasons).
    3.  *Request Update* (sends it back to the customer for more data).
*   **History:** Officers can view the historical log of all claims they have processed.

### D. Admin Module
**User Management:**
*   Admins can view a master list of all users and search for specific users by Email ID.
*   Admins manage account lifecycle by viewing Reactivation Requests from soft-deleted users and formally reactivating their accounts.

**Agent Management:**
*   Admins can add new Policy Agents and Claim Officers to the system.
*   Admins can edit the details or status of existing Agents and Officers.

**Policy Management:**
*   Admins have a global view of all policies active in the system.
*   Admins can search for specific policies using a unique Policy ID.

**Claim Management:**
*   **Distribution:** Admins have access to the "Claim Pool" (unassigned claims) and manually assign these claims to specific Claim Officers.
*   **Oversight:** Admins can view all claims across the system and search for specific claims using a Claim ID.

**Reporting:**
Admins can generate system-wide business reports, including:
*   Active Policies Report
*   Expired Policies Report
*   Approved Claims Report
*   Rejected Claims Report
*   Agent/Officer Performance Report

---

## 6. Business Rules & Validations
*   **Data Integrity:** A claim cannot be filed against an expired or cancelled policy.
*   **State Management:** Deleting a profile does not wipe the data from the database (Soft Delete). Instead, it flags the user as inactive to preserve policy and financial records.
*   **Segregation of Duties:** Policy Agents handle policy assignments/suggestions, while Claim Officers exclusively handle claims. Neither can do the other's job.
*   **Claim Workflow:** A claim cannot bypass the 'Pending' state unless acted upon by a designated Claim Officer.