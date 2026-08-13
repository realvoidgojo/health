# HIMS — Defect Log
**Module reviewed:** main application file (uses `database.py` for `fetch_all`, `fetch_one`, `execute_query`, `hash_password`, `get_input`, `validate_email`, `validate_date`, `validate_phone`)
**Note:** `database.py` was not provided, so items involving `validate_phone`, `validate_date`, `get_input` are flagged based on *observed symptoms* in the calling code and should be confirmed against that file.

| # | Severity | Location / Function | Defect Description |
|---|----------|---------------------|---------------------|
| 1 | High | `validate_phone()` (dependency, not shown) | Symptom in `register_user()` / `admin_agent_management()`: error message claims "10 digits with optional +91 prefix" but no visible enforcement in this file — needs confirmation that `database.py` actually rejects <10 or >10 digit strings, letters, or symbols. |
| 2 | High | `validate_date()` (dependency, not shown) | DOB format is only checked via this external function; no bounds check anywhere (e.g., future dates, DOB implying age > 120, or DOB after "created_at") are accepted if format is technically valid. |
| 3 | Medium | `get_input(..., is_password=True)` (dependency, not shown) | Cannot confirm from this file whether password entry is masked (no echo/asterisks) at the terminal — flagged per your note; verify implementation in `database.py`. |
| 4 | High | `register_user()` | Password has **no minimum length, complexity, or strength validation** at all. |
| 5 | Medium | `register_user()` | Email is not trimmed or lowercased before uniqueness check/storage → `User@x.com` and `user@x.com` can both register, causing duplicate-account confusion. |
| 6 | Medium | `login_user()` | Same email case-sensitivity issue — a user who registered with mixed case may fail to log in if they type a different case. |
| 7 | Low | `register_user()` | Agent auto-assignment uses `SELECT ... LIMIT 1` with **no ORDER BY** — assignment is arbitrary/non-deterministic and always biased to whichever row the DB returns first (no load balancing). |
| 8 | Low | `register_user()` | Email-uniqueness check (`SELECT` then `INSERT`) is a classic **TOCTOU race condition** — two near-simultaneous registrations with the same email could both pass the check. |
| 9 | High | `agent_dashboard()` → Reject flow | `sugg_id = int(sugg_id)` has **no try/except**. If the agent types non-numeric text instead of a Policy ID or leaving blank, this throws an unhandled `ValueError` and **crashes the entire application**. |
| 10 | High | `officer_dashboard()` → Review Claim | The claim lookup (`SELECT * FROM claims WHERE claim_id = ? AND claim_officer_id = ?`) does **not filter by status**. An officer can approve/reject/request-update on a claim that is already `APPROVED` or `REJECTED`, silently overwriting a final decision. |
| 11 | Medium | `admin_claim_management()` → Assign Claim | No check that the claim's current status is `PENDING_ASSIGNMENT` before assigning — an already-assigned or already-decided claim can be re-assigned/reset to `UNDER_REVIEW`, losing history. |
| 12 | High | `customer_claim_menu()` → File Claim | Claim amount is validated only against the **policy's total Sum Insured**, not against amounts already claimed/approved on that policy. Multiple claims can cumulatively exceed the Sum Insured. |
| 13 | Medium | `customer_claim_menu()` → File Claim | No check preventing a customer from filing **multiple simultaneous claims** on the same policy while one is already `PENDING_ASSIGNMENT` / `UNDER_REVIEW`. |
| 14 | Medium | `customer_policy_menu()` → Purchase Policy | `nominee` and `relation` fields accept **empty strings** — no validation that a nominee name/relation was actually entered. |
| 15 | Medium | `customer_policy_menu()` → Update Nominee | Same blank-value issue — nominee name/relation can be overwritten with empty strings. |
| 16 | Medium | `customer_policy_menu()` → Renew Policy | Leap-year edge case: `old_expiry.replace(year=old_expiry.year + 1)` throws `ValueError` for Feb 29 → non-leap year. The `except` block silently substitutes **today's date + 1 year** instead of a sane Feb 28/Mar 1 correction, producing an incorrect and inconsistent new expiry date. |
| 17 | Medium | `customer_policy_menu()` → Cancel Policy | Only `ACTIVE` policies can be cancelled; a customer **cannot cancel/withdraw a `PENDING_APPROVAL`** purchase request. |
| 18 | Low | `format_inr()` | Negative amounts are formatted incorrectly, e.g. `-500` → `"₹-5,500.00"`-style malformed grouping (the minus sign gets absorbed into the digit-grouping loop instead of prefixing the ₹ symbol). |
| 19 | Low | `format_inr()` | No handling for `None` input — `p['premium_amount'] / 12` in several report functions will throw an unhandled `TypeError` if a master policy record has a null premium. |
| 20 | Low | `print_card()` | Label column width is hardcoded to 18 characters, but several labels used elsewhere (e.g., `"Additional Details"`, `"Nominee Relation"`) are 17–19 characters, causing box misalignment for longer labels. |
| 21 | Low | `print_card()` | If `width` is small enough that `val_width = width - 22` goes ≤ 0, `textwrap.wrap()` raises a `ValueError` — no guard against this. |
| 22 | Medium | `customer_profile_menu()` | Sub-menu for "Edit Profile" has no `else` branch — entering an invalid `sub_choice` (e.g., 4, or non-numeric) silently does nothing with **no error message**, confusing the user. |
| 23 | Low | Most dashboard `while` loops (customer/agent/officer/admin) | Invalid main-menu choices (outside the listed numbers) print **no error message** — the loop just redisplays the header, leaving the user unsure if their input registered. |
| 24 | High | `admin_agent_management()` → Add Agent/Officer | Email entered is **never validated with `validate_email()`** (unlike `register_user()`), and there's **no uniqueness pre-check** — inconsistent with customer registration logic; a duplicate/malformed email only fails at the raw DB layer (if constrained at all). |
| 25 | Medium | `admin_agent_management()` → Add Agent/Officer | Password for staff accounts has **no strength/length validation**, same gap as customer registration. |
| 26 | High | `admin_agent_management()` → Edit Policy Agent/Claim Officer | The `view_callback` always calls `print_users_by_role('POLICY_AGENT')`, **even when editing a Claim Officer** — the on-screen reference list shown to the admin is wrong/misleading for that role. |
| 27 | Medium | `admin_user_management()` → Assign/Reassign Agent | Reassigning an agent updates `users.assigned_agent_id` and only `customer_policies` with status `PENDING_APPROVAL` — **existing `ACTIVE` policies keep the old agent**, leaving a customer's active policies and profile out of sync. |
| 28 | Low | `request_reactivation()` | Only handles the case where `is_deleted = 1`. A staff account disabled via "Toggle Active Status" (`is_active = 0`, `is_deleted = 0`) has **no self-service path back to active** — it's a dead end for that user. |
| 29 | Low | `login_user()` / general | No login-attempt throttling or lockout — unlimited password guesses are allowed (brute-force exposure), though CLI-scale risk is limited. |
| 30 | Medium | Various `execute_query` calls (agent approve/reject, officer review, admin claim-assign, admin agent-add) | Inconsistent error handling — customer-facing flows wrap DB writes in `try/except`, but several agent/officer/admin write operations do **not**, risking an unhandled exception and application crash on any DB error. |
| 31 | Low | `admin_claim_management()` → Search Claim by ID | Uses **inner JOINs** to `customer_policies` and `master_policies`; if either referenced row is ever removed, the claim silently disappears from search results instead of being shown with "N/A" fields. |
| 32 | Low | `officer_dashboard()` → Review Claim | If the officer enters an invalid action letter (not A/R/U), the remarks the officer just typed are **discarded with no way to retry without re-entering everything**, including re-navigating to the claim. |
| 33 | Medium | `customer_claim_menu()` → Update Claim | Status transition logic (`new_status = 'UNDER_REVIEW' if claim['status']=='NEEDS_UPDATE' else claim['status']`) means a claim in `PENDING_ASSIGNMENT` stays `PENDING_ASSIGNMENT` after "update" — the customer gets a success message but the record state didn't meaningfully change, which may be confusing/misleading. |
| 34 | Low | `agent_dashboard()` → Process Requests | Free-text `action` input only checks for `'A'`/`'R'` after `.upper()` — no loop/re-prompt on invalid input; the request is simply left unprocessed with only a generic error, forcing the agent to restart from the queue. |
| 35 | Low | General (all `float`/monetary inputs, e.g. Claim Amount) | `get_input(..., cast_type=float)` with no visible upper sanity bound — an absurdly large claim amount (bigger than any realistic Sum Insured but still under it, or negative-looking edge values) isn't cross-checked beyond the Sum Insured comparison. |

## Summary
- **Critical/High:** 6 (#1, #4, #9, #10, #12, #24, #26 — 7 actually, see table)
- **Medium:** ~15
- **Low:** ~13

**Top priorities to fix first:** #9 (unhandled crash), #10 (re-processing finalized claims), #12 (Sum Insured bypass via multiple claims), #16 (date logic bug), #26 (wrong reference list shown to admin), #1–#3 (confirm validation actually exists in `database.py`).
