# Flow Documentation: Health Insurance Management System (HIMS)

This document maps out the operational workflows, state machine transitions, and interaction sequences across all four user roles (Customer, Policy Agent, Claim Officer, Admin).

---

## 1. Account Lifecycle Flow

### 1.1 Registration & Authentication
```
[Unregistered User] 
        │
        ├──> (Select 1: Register) ──> Enter Email, Password, Name, DOB, Phone
        │                                       │
        │                                       ├──> Email exists? ──> (ERR: Existing Account)
        │                                       └──> Unique Email  ──> Create User Record 
        │                                                              (IsActive = True, IsDeleted = False)
        │
        └──> (Select 2: Login) ────> Enter Credentials (Email, Password)
                                                │
                                                ├──> Invalid Credentials ──> (ERR: Login Failed)
                                                ├──> IsDeleted = True    ──> (ERR: Account Deleted)
                                                ├──> IsActive = False     ──> (ERR: Pending Reactivation)
                                                └──> Valid & Active      ──> Redirect to Role Menu
```

### 1.2 Account Soft Delete & Reactivation
```
[Customer Menu]
        │
        ├──> (Option 5: Delete Account)
        │         │
        │         └──> System sets `IsDeleted = True`, `IsActive = False`
        │              User logged out automatically.
        │
        └──> (Option 6: Request Account Reactivation)
                  │
                  ├──> Enter Credentials
                  └──> Creates Record in `ReactivationRequests` (Status: 'Pending')
                                │
                                ▼
                      [Admin Dashboard]
                                │
                                ├──> Select Option 5: View Reactivation Requests
                                └──> Select Option 4: Reactivate User Account
                                          │
                                          └──> Sets `IsDeleted = False`, `IsActive = True`
                                               Sets Request Status = 'Approved'
                                               Customer can now log in again.
```

---

## 2. Policy Lifecycle & Agent Advisory Flow

### 2.1 Policy Purchase & Agent Approval Logic
```
[Customer]                                  [System/Database]                         [Policy Agent]
    │                                              │                                         │
    ├── View Available Policies ──────────────────>│                                         │
    │   (Individual/Family/Senior)                 │                                         │
    │                                              │                                         │
    ├── Request Purchase Policy ──────────────────>│ Record created in                       │
    │   (Enters Nominee info)                      │ `PolicyPurchases`                       │
    │                                              │ (Status: 'Pending_Approval')            │
    │                                              │                                         │
    │                                              │<──────────────── View Assigned Customers│
    │                                              │                               & Policies│
    │                                              │                                         │
    │                                              │<──────────────── Select Action:         │
    │                                              │                  1. Assign (Approve)    │
    │                                              │                     ──> Status = 'Active'│
    │                                              │                  2. Reject & Suggest    │
    │                                              │                     ──> Status = 'Rejected'│
    │                                              │                         Log Suggested   │
    │                                              │                         Policy ID       │
    │                                              │                                         │
    ├── View "Suggested Policies" <────────────────┼─────────────────────────────────────────┘
    │   (If agent rejected previous request)        │
    │                                              │
    └── View "My Policies" ───────────────────────>│ Returns Active/Expired/Cancelled policies
```

### 2.2 Policy Maintenance (Renewal, Nominee Update, Cancellation)
```
[Customer Menu]
        │
        ├──> Update Nominee Info ──> Input Policy ID ──> Check if Policy Active ──> Update Nominee Name
        │
        ├──> Renew Policy ─────────> Input Expired/Expiring Policy ID ──> Extend Expiry Date by +1 Year
        │                                                               ──> Set Status = 'Active'
        │
        └──> Cancel Policy ────────> Input Active Policy ID ─────────────> Set Status = 'Cancelled'
```

---

## 3. Claim Processing Lifecycle

### 3.1 End-to-End Claim Flow
```
[Customer]                      [Admin]                     [Claim Officer]
    │                              │                               │
    ├── 1. File Claim ────────────>│                               │
    │   (Select Policy, Amount,    │                               │
    │    Reason, Documents)        │                               │
    │                              │                               │
    │                     [Status: PENDING_ASSIGNMENT]             │
    │                              │                               │
    │                              ├── 2. Assign Claim Pool ──────>│
    │                              │   (Pick claim, assign to      │
    │                              │    Claim Officer ID)          │
    │                              │                               │
    │                              │                      [Status: UNDER_REVIEW]
    │                              │                               │
    │                              │<──────────────────────────────┤ 3. Review Claim
    │                              │                               │    Select Action:
    │                              │                               │    ├── Approve ──> Status: APPROVED
    │                              │                               │    ├── Reject  ──> Status: REJECTED
    │                              │                               │    └── Request ──> Status: NEEDS_UPDATE
    │                              │                               │        Update
    │<─────────────────────────────┼───────────────────────────────┤
    │                              │                               │
    ├── 4. If status == NEEDS_UPDATE                               │
    │   ├── Select "Update Claim Details"                          │
    │   └── Submit missing info/docs ─────────────────────────────>│ Re-enters Queue
    │                                                              │ (Status: UNDER_REVIEW)
    │                                                              │
    └── 5. View My Claims (Check final status)                     │
```

---

## 4. Admin Operations & Governance

```
                                  ┌────────────────────────┐
                                  │      ADMIN MENU        │
                                  └───────────┬────────────┘
                                              │
      ┌───────────────────────┬───────────────┴───────────────┬────────────────────────┐
      ▼                       ▼                               ▼                        ▼
[User Management]     [Agent Management]              [Claim Distribution]            [Reports]
  │                     │                               │                       │
  ├─ View All Users     ├─ Add/Edit Policy Agent        ├─ View Claim Pool      ├─ Active Policies
  ├─ Search Email       └─ Add/Edit Claim Officer       ├─ Assign Officer       ├─ Expired Policies
  └─ Reactivate                                         ├─ View All Claims      ├─ Approved Claims
     Accounts                                           └─ Search Claim ID      ├─ Rejected Claims
                                                                                └─ Agent Performance
```

---

## 5. State Transition Reference

### Account Status State Machine
| Initial State | Event / Trigger | Final State | Action Allowed |
| :--- | :--- | :--- | :--- |
| **New** | Customer Registers | `Active: True, Deleted: False` | Full system access |
| `Active: True` | Customer requests deletion | `Active: False, Deleted: True` | Blocked from login |
| `Deleted: True` | Customer requests reactivation | Reactivation Request logged | Login blocked (Pending Admin) |
| Reactivation Pending | Admin approves request | `Active: True, Deleted: False` | Access restored |

### Policy Status State Machine
| Initial State | Event / Trigger | Final State |
| :--- | :--- | :--- |
| **None** | Customer submits purchase request | `Pending_Approval` |
| `Pending_Approval` | Policy Agent approves purchase | `Active` |
| `Pending_Approval` | Policy Agent rejects purchase | `Rejected` |
| `Active` | Expiry date passed OR Customer cancels | `Expired` OR `Cancelled` |
| `Expired` | Customer pays for renewal | `Active` (Expiry extended) |

### Claim Status State Machine
| Initial State | Event / Trigger | Final State |
| :--- | :--- | :--- |
| **Submitted** | Customer files new claim | `PENDING_ASSIGNMENT` |
| `PENDING_ASSIGNMENT` | Admin assigns to Claim Officer | `UNDER_REVIEW` |
| `UNDER_REVIEW` | Claim Officer approves | `APPROVED` |
| `UNDER_REVIEW` | Claim Officer rejects | `REJECTED` |
| `UNDER_REVIEW` | Claim Officer requests more data | `NEEDS_UPDATE` |
| `NEEDS_UPDATE` | Customer provides updated info | `UNDER_REVIEW` |
