# Risk Register

## High-Risk Flows

1. **Authentication State & Global Variable Replacement**
   - **Risk:** The application heavily relies on `current_user` as a global variable. Passing this around via context or session objects might lead to missing arguments or stale state (e.g. if a user profile is updated but the session dict is not mutated).
   - **Mitigation:** Introduce a `Session` or `Context` object. Ensure profile updates mutate the object or reload it from the DB immediately. Add comprehensive auth integration tests.

2. **Policy Suggestions / Age Calculation**
   - **Risk:** The recent feature for suggesting policies based on age is embedded inside `customer_policy_menu`. Extracting it to a service might break the exact console formatting or default fallback rules (`age = 30` if parsing fails).
   - **Mitigation:** Extract age calculation into a pure function `calculate_age(dob: str) -> int` in `validators.py` or `formatting.py`. Create a `PolicyService.get_suggested_policies_by_age` method.

3. **Status Transitions (Claims & Policies)**
   - **Risk:** Directly updating statuses via SQL (`UPDATE claims SET status = ...`) is currently scattered. Centralizing this into a repository/service risks breaking the exact allowed transitions.
   - **Mitigation:** Define enums for statuses in `constants.py`. Write strict state machine checks in the service layer before allowing DB writes.

4. **Input Masking (`getpass_asterisk`)**
   - **Risk:** Cross-platform masking logic relies on `os` and `msvcrt`/`termios`. Moving it to a new structure might disrupt CLI experience.
   - **Mitigation:** Isolate `get_input` and `getpass_asterisk` carefully into `views/console/ui.py`.

## Edge Cases

1. **Reactivation Flow**
   - A soft-deleted user logs in. The system prompts them to request reactivation. If they already have a `PENDING` request, it must not create a duplicate. 
   - A user who is completely deleted (not just soft deleted, though there is no hard delete flow currently) might trigger unexpected bugs.

2. **Claim Constraints**
   - A claim amount must be strictly <= `sum_insured`. The join logic (`customer_policies` -> `master_policies`) must be preserved perfectly.
   - Claims can only be filed against `ACTIVE` policies. What if a policy expires *while* a claim is `UNDER_REVIEW`? Currently, there are no checks blocking processing of claims for expired policies, only for *filing* them.

3. **Database Concurrency & Connections**
   - Currently, `execute_query` opens and closes connections per query. Introducing a `BaseRepository` might change connection lifecycle. 
   - **Mitigation:** Use context managers (`with get_db_connection():`) per repository method or per service transaction.

## Existing Test Gaps
- `test_app.py` has heavily mocked `builtins.input`. If prompts change even slightly (e.g., adding an extra space), tests might break.
- **Mitigation:** Carefully port `test_app.py`. The prompts in `ui.py` must match exactly the legacy prompts, or we must update the tests to mock inputs sequentially based on the new logic flow. We will port tests module by module and ensure they pass.
