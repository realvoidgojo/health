# SQL Inventory

## 1. User Domain (`users`)
- `SELECT * FROM users WHERE email = ?` (Unique check)
- `INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id) VALUES (...)` (Register Customer)
- `INSERT INTO users (...) VALUES (...)` (Admin add staff)
- `SELECT * FROM users WHERE email = ? AND password = ?` (Login auth check)
- `SELECT * FROM users WHERE role = ? AND is_deleted = 0` (Get by role)
- `SELECT user_id, full_name, email, role, is_active FROM users WHERE role IN ('POLICY_AGENT', 'CLAIM_OFFICER') AND is_deleted = 0` (Get Staff)
- `UPDATE users SET full_name/phone/date_of_birth = ? WHERE user_id = ?` (Profile updates)
- `UPDATE users SET is_deleted = 1, is_active = 0 WHERE user_id = ?` (Soft delete)
- `SELECT user_id FROM users WHERE role = 'POLICY_AGENT' AND is_active = 1 LIMIT 1` (Random agent assignment fallback)

## 2. Policy Domain (`master_policies`, `customer_policies`)
- `SELECT * FROM master_policies WHERE is_active = 1`
- `SELECT * FROM master_policies WHERE category = ? AND is_active = 1` (Age-based suggestions)
- `SELECT cp.*, mp.policy_name FROM customer_policies cp JOIN master_policies mp ON cp.policy_id = mp.policy_id WHERE cp.customer_id = ?` (My Policies)
- `SELECT * FROM customer_policies WHERE customer_id = ? AND policy_id = ? AND status IN ('PENDING_APPROVAL', 'ACTIVE')` (Duplicate purchase check)
- `INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id) VALUES (...)` (Purchase request)
- `UPDATE customer_policies SET nominee_name = ?, nominee_relation = ? WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'`
- `UPDATE customer_policies SET status = 'ACTIVE', expiry_date = ? WHERE customer_policy_id = ?` (Renew)
- `UPDATE customer_policies SET status = 'CANCELLED' WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'` (Cancel)
- `SELECT cp.*, u.full_name as cust_name, mp.policy_name FROM customer_policies cp JOIN users u ON cp.customer_id = u.user_id JOIN master_policies mp ON cp.policy_id = mp.policy_id WHERE cp.assigned_agent_id = ? AND cp.status = 'PENDING_APPROVAL'` (Agent review queue)
- `UPDATE customer_policies SET status = ?, start_date = ?, expiry_date = ?, agent_remarks = ?, suggested_policy_id = ? WHERE customer_policy_id = ?` (Agent approve/reject)

## 3. Claim Domain (`claims`, `claim_history`)
- `SELECT * FROM claims WHERE customer_id = ?` (My claims)
- `SELECT cp.status, mp.sum_insured FROM customer_policies cp JOIN master_policies mp ON cp.policy_id = mp.policy_id WHERE cp.customer_policy_id = ? AND cp.customer_id = ?` (Validate claim rules)
- `INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason) VALUES (...)`
- `SELECT status FROM claims WHERE claim_id = ? AND customer_id = ?` (Check before update details)
- `UPDATE claims SET additional_details = ?, status = ? WHERE claim_id = ?` (Customer update)
- `INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (...)`
- `SELECT c.*, u.full_name as cust_name, cp.policy_id FROM claims c JOIN users u ON c.customer_id = u.user_id JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id WHERE c.status = 'PENDING_ASSIGNMENT'` (Admin view unassigned)
- `UPDATE claims SET claim_officer_id = ?, status = 'UNDER_REVIEW' WHERE claim_id = ?` (Admin assign)
- `SELECT c.*, u.full_name as cust_name, o.full_name as officer_name, mp.policy_name FROM claims c JOIN users u ON c.customer_id = u.user_id LEFT JOIN users o ON c.claim_officer_id = o.user_id JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id JOIN master_policies mp ON cp.policy_id = mp.policy_id` (View all claims)

## 4. Reactivation Domain (`reactivation_requests`)
- `SELECT * FROM reactivation_requests WHERE user_id = ? AND status = 'PENDING'`
- `INSERT INTO reactivation_requests (user_id) VALUES (?)`
- `SELECT r.*, u.email FROM reactivation_requests r JOIN users u ON r.user_id = u.user_id WHERE r.status = 'PENDING'`
- `UPDATE reactivation_requests SET status = ?, admin_remarks = ? WHERE request_id = ?`

## 5. Reports Domain (Aggregations)
- `SELECT COUNT(*) FROM customer_policies WHERE status = 'ACTIVE'`
- `SELECT COUNT(*), SUM(claim_amount) FROM claims WHERE status = 'APPROVED'`
- `SELECT COUNT(*) FROM customer_policies WHERE status = 'EXPIRED'`
- `SELECT COUNT(*), SUM(claim_amount) FROM claims WHERE status = 'REJECTED'`
