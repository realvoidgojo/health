# Business Rules & Constraints

## 1. Role-Based Access Rules
- **CUSTOMER**: Can manage own profile, own policies, and own claims. Cannot access other users' data.
- **POLICY_AGENT**: Reviews pending policies assigned to them (`assigned_agent_id`).
- **CLAIM_OFFICER**: Reviews claims assigned to them (`claim_officer_id`).
- **ADMIN**: Global access to manage users, assign agents/officers, reactivate accounts, and generate reports.

## 2. Account States
- **Active**: `is_active=1`, `is_deleted=0`. Can log in and perform actions.
- **Deleted**: `is_active=0`, `is_deleted=1`. Cannot log in. Redirected to reactivation prompt.
- **Reactivation Request**: 
  - Statuses: `PENDING`, `APPROVED`, `REJECTED`.
  - Admin approval resets the user to active (`is_active=1`, `is_deleted=0`).

## 3. Policy Lifecycle States (`customer_policies.status`)
- **PENDING_APPROVAL**: Created upon purchase request. Awaiting agent review.
- **ACTIVE**: Approved by agent. Only state where nominee updates and claim filing are allowed.
- **EXPIRED**: The current date is past `expiry_date`. Allowed transition: Renew (sets to `ACTIVE` and adds 1 year).
- **CANCELLED**: Cancelled by customer. Terminal state.
- **REJECTED**: Rejected by agent. Terminal state. Can optionally have a `suggested_policy_id` tied to it.

## 4. Claim Lifecycle States (`claims.status`)
- **PENDING_ASSIGNMENT**: Initial state when customer files a claim. Awaiting admin assignment.
- **UNDER_REVIEW**: Assigned to an officer (`claim_officer_id` is NOT NULL).
- **NEEDS_UPDATE**: Officer requested more details. Customer can update `additional_details`, sending it back to `UNDER_REVIEW`.
- **APPROVED**: Terminal success state.
- **REJECTED**: Terminal failure state.

## 5. Allowed Transitions & Blockers
- **Duplicate Policy**: Customer cannot purchase the same policy if they already have one in `PENDING_APPROVAL` or `ACTIVE` state.
- **Claim Limits**: Claim amount must not exceed the `sum_insured` of the associated `master_policy`.
- **Claim Dependency**: Claims can only be filed against `ACTIVE` policies.
- **Nominee Update**: Only allowed if policy is `ACTIVE`.

## 6. Validation Rules
- **Email**: Must conform to standard email regex `^[\w\.-]+@[\w\.-]+\.\w+$`. Must be unique in the database.
- **Phone**: Exactly 10 digits, optional `+91` prefix (e.g., `+91 9876543210`).
- **Date**: Format must be `YYYY-MM-DD`. Validated across DOB and expiry calculations.
- **Input Types**: `cast_type` is heavily used to enforce `int` or `float` during prompts.

## 7. Agent Assignment
- On registration, a CUSTOMER is randomly assigned an active `POLICY_AGENT`.
- All policy purchases default to `assigned_agent_id` from the customer's profile.
- Admin can reassign agents.

## 8. Report Logic
- Active Policies: Count where `status = 'ACTIVE'`.
- Approved Claims: Count where `status = 'APPROVED'`, aggregated by sum.
- Expired Policies: Count where `status = 'EXPIRED'`.
- Rejected Claims: Count where `status = 'REJECTED'`.
