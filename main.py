import sys
import textwrap
from datetime import datetime
from database import fetch_all, fetch_one, execute_query, hash_password, get_input, print_success, print_error, print_warning, print_info, Colors

current_user = None

def format_inr(amount):
    """Formats monetary amounts into Indian Rupee format (e.g. ₹5,00,000.00)."""
    s = f"{float(amount):.2f}"
    parts = s.split('.')
    integer_part, decimal_part = parts[0], parts[1]
    
    if len(integer_part) <= 3:
        return f"₹{integer_part}.{decimal_part}"
    
    last_three = integer_part[-3:]
    other_digits = integer_part[:-3]
    
    res = ""
    while len(other_digits) > 2:
        res = "," + other_digits[-2:] + res
        other_digits = other_digits[:-2]
    if other_digits:
        res = other_digits + res
    return f"₹{res},{last_three}.{decimal_part}"

def display_header(title):
    print(f"\n{Colors.CYAN}{'='*58}{Colors.RESET}")
    print(f"{Colors.CYAN}{title.center(58)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*58}{Colors.RESET}")

def print_card(title, fields, width=58):
    """Prints a structured, beautifully formatted ASCII card for object details."""
    print(f"\n{Colors.CYAN}┌{'─' * width}┐{Colors.RESET}")
    title_str = f" {title}"
    padding = width - len(title_str)
    if padding < 0:
        title_str = title_str[:width]
        padding = 0
    print(f"{Colors.CYAN}│{Colors.RESET}{Colors.YELLOW}{title_str}{' '*padding}{Colors.RESET}{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}├{'─' * width}┤{Colors.RESET}")
    for label, val in fields:
        val_str = str(val) if val is not None else "N/A"
        line_str = f" {label:<18}: {val_str}"
        pad = width - len(line_str)
        if pad < 0:
            line_str = line_str[:width]
            pad = 0
        print(f"{Colors.CYAN}│{Colors.RESET}{line_str}{' '*pad}{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}└{'─' * width}┘{Colors.RESET}")

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
def register_user():
    display_header("REGISTER NEW ACCOUNT")
    name = get_input("Full Name: ")
    email = get_input("Email Address: ")
    password = get_input("Password: ", is_password=True)
    phone = get_input("Phone Number: ")
    dob = get_input("Date of Birth (YYYY-MM-DD): ")
    
    # Check if email exists
    existing = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if existing:
        print_error("An account with this email already exists.")
        return
        
    hashed_pw = hash_password(password)
    
    # Check if we should assign an agent (randomly or pick first for simplicity)
    # Get any agent
    agent = fetch_one("SELECT user_id FROM users WHERE role = 'POLICY_AGENT' AND is_active = 1 LIMIT 1")
    agent_id = agent['user_id'] if agent else None
    
    try:
        user_id = execute_query(
            "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, email, hashed_pw, phone, dob, 'CUSTOMER', agent_id)
        )
        print_success(f"Registration successful! Your user ID is {user_id}")
    except Exception as e:
        print_error(f"Failed to register: {e}")

def login_user():
    global current_user
    display_header("LOGIN")
    email = get_input("Email: ")
    password = get_input("Password: ", is_password=True)
    
    hashed_pw = hash_password(password)
    user = fetch_one("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
    
    if not user:
        print_error("Invalid email or password.")
        return False
        
    if user['is_deleted'] == 1:
        print_error("This account has been deleted. Please request reactivation.")
        return False
        
    if user['is_active'] == 0:
        print_error("This account is inactive or pending reactivation.")
        return False
        
    current_user = dict(user)
    print_success(f"Welcome back, {current_user['full_name']}!")
    return True

def request_reactivation():
    display_header("REQUEST ACCOUNT REACTIVATION")
    email = get_input("Email: ")
    password = get_input("Password: ", is_password=True)
    
    hashed_pw = hash_password(password)
    user = fetch_one("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
    
    if not user:
        print_error("Invalid email or password.")
        return
        
    if user['is_deleted'] == 0:
        print_error("Account is already active. You can log in normally.")
        return
        
    existing_request = fetch_one("SELECT * FROM reactivation_requests WHERE user_id = ? AND status = 'PENDING'", (user['user_id'],))
    if existing_request:
        print_warning("You already have a pending reactivation request.")
        return
        
    try:
        execute_query("INSERT INTO reactivation_requests (user_id) VALUES (?)", (user['user_id'],))
        print_success("Reactivation request submitted successfully. Please wait for admin approval.")
    except Exception as e:
        print_error(f"Failed to submit request: {e}")

# ---------------------------------------------------------
# CUSTOMER MODULE
# ---------------------------------------------------------
def customer_profile_menu():
    global current_user
    while True:
        display_header("CUSTOMER PROFILE")
        print("1. View Profile")
        print("2. Edit Profile")
        print("3. Delete Account")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            print_card(f"PROFILE: {current_user['full_name']}", [
                ("User ID", current_user['user_id']),
                ("Email", current_user['email']),
                ("Phone", current_user['phone']),
                ("Date of Birth", current_user['date_of_birth']),
                ("Role", current_user['role'])
            ])
        elif choice == 2:
            print("\n1. Update Name")
            print("2. Update Phone")
            print("3. Update Date of Birth")
            print("0. Cancel")
            sub_choice = get_input("Select field to update: ", cast_type=int)
            
            try:
                if sub_choice == 1:
                    new_val = get_input("New Name: ")
                    execute_query("UPDATE users SET full_name = ? WHERE user_id = ?", (new_val, current_user['user_id']))
                    current_user['full_name'] = new_val
                    print_success("Profile updated.")
                elif sub_choice == 2:
                    new_val = get_input("New Phone Number: ")
                    execute_query("UPDATE users SET phone = ? WHERE user_id = ?", (new_val, current_user['user_id']))
                    current_user['phone'] = new_val
                    print_success("Profile updated.")
                elif sub_choice == 3:
                    new_val = get_input("New DOB (YYYY-MM-DD): ")
                    execute_query("UPDATE users SET date_of_birth = ? WHERE user_id = ?", (new_val, current_user['user_id']))
                    current_user['date_of_birth'] = new_val
                    print_success("Profile updated.")
            except Exception as e:
                print_error(f"Failed to update profile: {e}")
        elif choice == 3:
            confirm = get_input("Are you sure you want to delete your account? (Y/N): ")
            if confirm.upper() == 'Y':
                try:
                    execute_query("UPDATE users SET is_deleted = 1, is_active = 0 WHERE user_id = ?", (current_user['user_id'],))
                    print_success("Account deleted successfully.")
                    current_user = None
                    return True # Signifies logged out
                except Exception as e:
                    print_error(f"Failed to delete account: {e}")
        elif choice == 0:
            break
    return False

def customer_policy_menu():
    while True:
        display_header("POLICY MANAGEMENT")
        print("1. View Available Policies")
        print("2. Purchase Policy")
        print("3. View My Policies")
        print("4. View Suggested Policies")
        print("5. Update Nominee")
        print("6. Renew Policy")
        print("7. Cancel Policy")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            policies = fetch_all("SELECT * FROM master_policies WHERE is_active = 1")
            CARD_WIDTH = 58
            INNER_WIDTH = 54
            
            for p in policies:
                print(f"{Colors.CYAN}┌{'─' * CARD_WIDTH}┐{Colors.RESET}")
                
                # Header row
                header_text = f" [{p['policy_id']}] {p['policy_name']}"
                print(f"{Colors.CYAN}│{Colors.RESET}{Colors.GREEN}{header_text.ljust(CARD_WIDTH)}{Colors.RESET}{Colors.CYAN}│{Colors.RESET}")
                print(f"{Colors.CYAN}├{'─' * CARD_WIDTH}┤{Colors.RESET}")
                
                # Fields
                cat_line = f" Category    : {p['category']}"
                sum_line = f" Sum Insured : {format_inr(p['sum_insured'])}"
                prem_line = f" Premium     : {format_inr(p['premium_amount'])}"
                det_title = " Coverage Details:"
                
                print(f"{Colors.CYAN}│{Colors.RESET}{cat_line.ljust(CARD_WIDTH)}{Colors.CYAN}│{Colors.RESET}")
                print(f"{Colors.CYAN}│{Colors.RESET}{sum_line.ljust(CARD_WIDTH)}{Colors.CYAN}│{Colors.RESET}")
                print(f"{Colors.CYAN}│{Colors.RESET}{prem_line.ljust(CARD_WIDTH)}{Colors.CYAN}│{Colors.RESET}")
                print(f"{Colors.CYAN}│{Colors.RESET}{det_title.ljust(CARD_WIDTH)}{Colors.CYAN}│{Colors.RESET}")
                
                wrapped_details = textwrap.wrap(p['coverage_details'], width=INNER_WIDTH)
                for line in wrapped_details:
                    d_line = f"   • {line}"
                    print(f"{Colors.CYAN}│{Colors.RESET}{d_line.ljust(CARD_WIDTH)}{Colors.CYAN}│{Colors.RESET}")
                    
                print(f"{Colors.CYAN}└{'─' * CARD_WIDTH}┘{Colors.RESET}\n")
        elif choice == 2:
            policy_id = get_input("Enter Policy ID to purchase: ", cast_type=int)
            master = fetch_one("SELECT * FROM master_policies WHERE policy_id = ? AND is_active = 1", (policy_id,))
            if not master:
                print_error("Invalid or inactive Policy ID.")
                continue
                
            nominee = get_input("Nominee Name: ")
            relation = get_input("Nominee Relation: ")
            try:
                execute_query(
                    "INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id) VALUES (?, ?, ?, ?, ?)",
                    (current_user['user_id'], policy_id, nominee, relation, current_user['assigned_agent_id'])
                )
                print_success("Policy purchase requested successfully! Pending agent approval.")
            except Exception as e:
                print_error(f"Failed to purchase policy: {e}")
        elif choice == 3:
            policies = fetch_all("SELECT cp.*, mp.policy_name FROM customer_policies cp JOIN master_policies mp ON cp.policy_id = mp.policy_id WHERE cp.customer_id = ?", (current_user['user_id'],))
            if not policies:
                print_info("No policies found.")
            for p_row in policies:
                p = dict(p_row)
                print_card(f"POLICY #{p['customer_policy_id']} - {p['policy_name']}", [
                    ("Status", p['status']),
                    ("Nominee Name", p['nominee_name']),
                    ("Nominee Relation", p.get('nominee_relation', 'N/A')),
                    ("Start Date", p.get('start_date') or 'Pending'),
                    ("Expiry Date", p.get('expiry_date') or 'Pending'),
                    ("Agent Remarks", p.get('agent_remarks') or 'None')
                ])
        elif choice == 4:
            policies = fetch_all("SELECT cp.*, mp.policy_name FROM customer_policies cp JOIN master_policies mp ON cp.suggested_policy_id = mp.policy_id WHERE cp.customer_id = ? AND cp.status = 'REJECTED' AND cp.suggested_policy_id IS NOT NULL", (current_user['user_id'],))
            if not policies:
                print_info("No suggested policies.")
            for p_row in policies:
                p = dict(p_row)
                print_card(f"SUGGESTION FOR REQUEST #{p['customer_policy_id']}", [
                    ("Suggested Plan ID", p['suggested_policy_id']),
                    ("Suggested Plan", p['policy_name']),
                    ("Agent Remarks", p.get('agent_remarks') or 'None')
                ])
        elif choice == 5:
            cp_id = get_input("Enter Customer Policy ID: ", cast_type=int)
            new_nominee = get_input("New Nominee Name: ")
            new_relation = get_input("New Nominee Relation: ")
            try:
                rows = execute_query("UPDATE customer_policies SET nominee_name = ?, nominee_relation = ? WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'", (new_nominee, new_relation, cp_id, current_user['user_id']))
                if rows > 0:
                    print_success("Nominee updated.")
                else:
                    print_error("Policy not found or not ACTIVE.")
            except Exception as e:
                print_error(f"Failed to update nominee: {e}")
        elif choice == 6:
            cp_id = get_input("Enter Customer Policy ID to renew: ", cast_type=int)
            policy = fetch_one("SELECT * FROM customer_policies WHERE customer_policy_id = ? AND customer_id = ?", (cp_id, current_user['user_id']))
            if not policy:
                print_error("Policy not found.")
                continue
            if policy['status'] != 'EXPIRED':
                print_error("Only EXPIRED policies can be renewed.")
                continue
                
            try:
                # Add 1 year to expiry date
                old_expiry = datetime.strptime(policy['expiry_date'], "%Y-%m-%d")
                new_expiry = old_expiry.replace(year=old_expiry.year + 1).strftime("%Y-%m-%d")
            except Exception:
                new_expiry = datetime.now().replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")
                
            try:
                execute_query("UPDATE customer_policies SET status = 'ACTIVE', expiry_date = ? WHERE customer_policy_id = ?", (new_expiry, cp_id))
                print_success(f"Policy renewed. New expiry date: {new_expiry}")
            except Exception as e:
                print_error(f"Failed to renew policy: {e}")
        elif choice == 7:
            cp_id = get_input("Enter Customer Policy ID to cancel: ", cast_type=int)
            try:
                rows = execute_query("UPDATE customer_policies SET status = 'CANCELLED' WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'", (cp_id, current_user['user_id']))
                if rows > 0:
                    print_success("Policy cancelled.")
                else:
                    print_error("Policy not found or not ACTIVE.")
            except Exception as e:
                print_error(f"Failed to cancel policy: {e}")
        elif choice == 0:
            break

def customer_claim_menu():
    while True:
        display_header("CLAIM MANAGEMENT")
        print("1. File Claim")
        print("2. View My Claims")
        print("3. Update Claim Details")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            cp_id = get_input("Enter Customer Policy ID against which to claim: ", cast_type=int)
            # Check if policy is active
            pol = fetch_one("SELECT status FROM customer_policies WHERE customer_policy_id = ? AND customer_id = ?", (cp_id, current_user['user_id']))
            if not pol or pol['status'] != 'ACTIVE':
                print_error("You can only file claims against ACTIVE policies.")
                continue
                
            amount = get_input("Claim Amount: ", cast_type=float)
            reason = get_input("Claim Reason: ")
            try:
                execute_query(
                    "INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason) VALUES (?, ?, ?, ?)",
                    (cp_id, current_user['user_id'], amount, reason)
                )
                print_success("Claim filed successfully. Pending assignment.")
            except Exception as e:
                print_error(f"Failed to file claim: {e}")
        elif choice == 2:
            claims = fetch_all("SELECT * FROM claims WHERE customer_id = ?", (current_user['user_id'],))
            if not claims:
                print_info("No claims filed.")
            for c_row in claims:
                c = dict(c_row)
                print_card(f"CLAIM #{c['claim_id']}", [
                    ("Policy ID", c['customer_policy_id']),
                    ("Claim Amount", format_inr(c['claim_amount'])),
                    ("Status", c['status']),
                    ("Claim Reason", c['claim_reason']),
                    ("Officer Remarks", c.get('officer_remarks') or 'None')
                ])
        elif choice == 3:
            claim_id = get_input("Enter Claim ID to update: ", cast_type=int)
            claim = fetch_one("SELECT status FROM claims WHERE claim_id = ? AND customer_id = ?", (claim_id, current_user['user_id']))
            if not claim or claim['status'] != 'NEEDS_UPDATE':
                print_error("Claim does not need an update or does not exist.")
                continue
                
            details = get_input("Provide Additional Details: ")
            try:
                execute_query("UPDATE claims SET additional_details = ?, status = 'UNDER_REVIEW' WHERE claim_id = ?", (details, claim_id))
                print_success("Claim updated successfully.")
                
                # Log to claim history that customer updated
                execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim_id, current_user['user_id'], 'CUSTOMER_UPDATED', 'Customer updated claim details'))
            except Exception as e:
                print_error(f"Failed to update claim: {e}")
        elif choice == 0:
            break

def customer_dashboard():
    global current_user
    while current_user:
        display_header("CUSTOMER DASHBOARD")
        print("1. Profile Management")
        print("2. Policy Management")
        print("3. Claim Management")
        print("0. Logout")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            if customer_profile_menu():
                break # Account deleted
        elif choice == 2:
            customer_policy_menu()
        elif choice == 3:
            customer_claim_menu()
        elif choice == 0:
            current_user = None
            break

# ---------------------------------------------------------
# POLICY AGENT MODULE
# ---------------------------------------------------------
def agent_dashboard():
    global current_user
    while current_user:
        display_header("POLICY AGENT DASHBOARD")
        print("1. View Assigned Customers")
        print("2. View Assigned Customer Policies")
        print("3. Process Policy Requests (Approve/Reject)")
        print("0. Logout")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            customers = fetch_all("SELECT * FROM users WHERE assigned_agent_id = ? AND is_deleted = 0", (current_user['user_id'],))
            if not customers:
                print_info("No assigned customers.")
            for c in customers:
                print_card(f"CUSTOMER #{c['user_id']} - {c['full_name']}", [
                    ("Email", c['email']),
                    ("Phone", c['phone']),
                    ("Date of Birth", c['date_of_birth'])
                ])
        elif choice == 2:
            policies = fetch_all("SELECT cp.*, u.full_name FROM customer_policies cp JOIN users u ON cp.customer_id = u.user_id WHERE cp.assigned_agent_id = ?", (current_user['user_id'],))
            if not policies:
                print_info("No assigned customer policies.")
            for p in policies:
                print_card(f"CUSTOMER POLICY #{p['customer_policy_id']}", [
                    ("Customer", p['full_name']),
                    ("Master Policy ID", p['policy_id']),
                    ("Status", p['status']),
                    ("Nominee", f"{p['nominee_name']} ({p['nominee_relation']})")
                ])
        elif choice == 3:
            requests = fetch_all("SELECT cp.*, u.full_name FROM customer_policies cp JOIN users u ON cp.customer_id = u.user_id WHERE cp.assigned_agent_id = ? AND cp.status = 'PENDING_APPROVAL'", (current_user['user_id'],))
            if not requests:
                print_info("No pending policy requests.")
                continue
            for r in requests:
                print_card(f"PENDING APPROVAL #{r['customer_policy_id']}", [
                    ("Customer", r['full_name']),
                    ("Policy ID", r['policy_id']),
                    ("Nominee", f"{r['nominee_name']} ({r['nominee_relation']})")
                ])
                
            req_id = get_input("Enter Request ID to process: ", cast_type=int)
            action = get_input("Action (A=Approve, R=Reject): ").upper()
            
            if action == 'A':
                execute_query("UPDATE customer_policies SET status = 'ACTIVE' WHERE customer_policy_id = ?", (req_id,))
                print_success("Policy approved.")
            elif action == 'R':
                sugg_id = get_input("Suggest alternative Policy ID (optional, press enter to skip): ", allow_empty=True)
                sugg_id = int(sugg_id) if sugg_id else None
                reason = get_input("Rejection Remarks: ")
                execute_query("UPDATE customer_policies SET status = 'REJECTED', suggested_policy_id = ?, agent_remarks = ? WHERE customer_policy_id = ?", (sugg_id, reason, req_id))
                print_success("Policy rejected.")
            else:
                print_error("Invalid action.")
        elif choice == 0:
            current_user = None
            break

# ---------------------------------------------------------
# CLAIM OFFICER MODULE
# ---------------------------------------------------------
def officer_dashboard():
    global current_user
    while current_user:
        display_header("CLAIM OFFICER DASHBOARD")
        print("1. View Assigned Claims Queue")
        print("2. Review Claim")
        print("3. View Claim History Log")
        print("0. Logout")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            claims = fetch_all("SELECT * FROM claims WHERE claim_officer_id = ? AND status = 'UNDER_REVIEW'", (current_user['user_id'],))
            if not claims:
                print_info("No claims in queue.")
            for c in claims:
                print_card(f"CLAIM QUEUE #{c['claim_id']}", [
                    ("Customer ID", c['customer_id']),
                    ("Policy ID", c['customer_policy_id']),
                    ("Claim Amount", format_inr(c['claim_amount'])),
                    ("Claim Reason", c['claim_reason'])
                ])
        elif choice == 2:
            claim_id = get_input("Enter Claim ID to review: ", cast_type=int)
            claim = fetch_one("SELECT * FROM claims WHERE claim_id = ? AND claim_officer_id = ?", (claim_id, current_user['user_id']))
            if not claim:
                print_error("Claim not found or not assigned to you.")
                continue
                
            print("\nOptions: [A] Approve | [R] Reject | [U] Request Update")
            action = get_input("Select action: ").upper()
            remarks = get_input("Remarks: ")
            
            status_map = {'A': 'APPROVED', 'R': 'REJECTED', 'U': 'NEEDS_UPDATE'}
            action_map = {'A': 'APPROVED', 'R': 'REJECTED', 'U': 'REQUESTED_UPDATE'}
            
            if action in status_map:
                execute_query("UPDATE claims SET status = ?, officer_remarks = ? WHERE claim_id = ?", (status_map[action], remarks, claim_id))
                execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim_id, current_user['user_id'], action_map[action], remarks))
                print_success(f"Claim marked as {status_map[action]}.")
            else:
                print_error("Invalid action.")
        elif choice == 3:
            logs = fetch_all("SELECT * FROM claim_history WHERE officer_id = ?", (current_user['user_id'],))
            if not logs:
                print_info("No history logs.")
            for log_row in logs:
                log = dict(log_row)
                print_card(f"AUDIT LOG #{log['history_id']}", [
                    ("Claim ID", log['claim_id']),
                    ("Action Taken", log['action_taken']),
                    ("Remarks", log.get('remarks') or 'None'),
                    ("Timestamp", log['action_timestamp'])
                ])
        elif choice == 0:
            current_user = None
            break

# ---------------------------------------------------------
# ADMIN MODULE
# ---------------------------------------------------------
def admin_user_management():
    while True:
        display_header("USER MANAGEMENT")
        print("1. View All Users")
        print("2. Search by Email")
        print("3. View Reactivation Requests")
        print("4. Assign/Reassign Policy Agent")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            users = fetch_all("SELECT user_id, full_name, email, role, is_active, is_deleted FROM users")
            if not users:
                print_info("No users found.")
            for u in users:
                status_str = "Active" if u['is_active'] == 1 and u['is_deleted'] == 0 else ("Deleted" if u['is_deleted'] == 1 else "Inactive")
                print_card(f"USER #{u['user_id']} - {u['full_name']}", [
                    ("Email", u['email']),
                    ("Role", u['role']),
                    ("Status", status_str)
                ])
        elif choice == 2:
            email = get_input("Enter Email: ")
            user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
            if user:
                status_str = "Active" if user['is_active'] == 1 and user['is_deleted'] == 0 else ("Deleted" if user['is_deleted'] == 1 else "Inactive")
                print_card(f"USER DETAILS #{user['user_id']}", [
                    ("Full Name", user['full_name']),
                    ("Email", user['email']),
                    ("Phone", user['phone']),
                    ("Date of Birth", user['date_of_birth']),
                    ("Role", user['role']),
                    ("Assigned Agent ID", user['assigned_agent_id'] or "None"),
                    ("Account Status", status_str),
                    ("Created At", user['created_at'])
                ])
            else:
                print_error("User not found.")
        elif choice == 3:
            requests = fetch_all("SELECT r.*, u.email FROM reactivation_requests r JOIN users u ON r.user_id = u.user_id WHERE r.status = 'PENDING'")
            if not requests:
                print_info("No pending requests.")
                continue
            for r in requests:
                print_card(f"REACTIVATION REQUEST #{r['request_id']}", [
                    ("User Email", r['email']),
                    ("User ID", r['user_id']),
                    ("Status", r['status']),
                    ("Request Date", r['request_date'])
                ])
            req_id = get_input("Enter Request ID to process (0 to cancel): ", cast_type=int)
            if req_id != 0:
                req = fetch_one("SELECT * FROM reactivation_requests WHERE request_id = ?", (req_id,))
                if req:
                    action = get_input("Action [A=Approve, R=Reject]: ").upper()
                    remarks = get_input("Remarks: ")
                    if action == 'A':
                        execute_query("UPDATE users SET is_deleted = 0, is_active = 1 WHERE user_id = ?", (req['user_id'],))
                        execute_query("UPDATE reactivation_requests SET status = 'APPROVED', admin_remarks = ? WHERE request_id = ?", (remarks, req_id))
                        print_success("User account reactivated.")
                    elif action == 'R':
                        execute_query("UPDATE reactivation_requests SET status = 'REJECTED', admin_remarks = ? WHERE request_id = ?", (remarks, req_id))
                        print_success("Reactivation request rejected.")
                    else:
                        print_error("Invalid action.")
        elif choice == 4:
            c_id = get_input("Enter Customer User ID: ", cast_type=int)
            customer = fetch_one("SELECT * FROM users WHERE user_id = ? AND role = 'CUSTOMER'", (c_id,))
            if not customer:
                print_error("Customer not found.")
                continue
                
            agents = fetch_all("SELECT user_id, full_name FROM users WHERE role = 'POLICY_AGENT' AND is_active = 1")
            print("\nAvailable Policy Agents:")
            for a in agents:
                print(f"Agent ID: {a['user_id']} | Name: {a['full_name']}")
                
            a_id = get_input("Enter Policy Agent ID to assign: ", cast_type=int)
            try:
                execute_query("UPDATE users SET assigned_agent_id = ? WHERE user_id = ?", (a_id, c_id))
                execute_query("UPDATE customer_policies SET assigned_agent_id = ? WHERE customer_id = ? AND status = 'PENDING_APPROVAL'", (a_id, c_id))
                print_success("Agent assigned successfully.")
            except Exception as e:
                print_error(f"Failed to assign agent: {e}")
        elif choice == 0:
            break

def admin_agent_management():
    while True:
        display_header("AGENT MANAGEMENT")
        print("1. Add Policy Agent / Claim Officer")
        print("2. View All Agents/Officers")
        print("3. Edit Policy Agent / Claim Officer")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            name = get_input("Full Name: ")
            email = get_input("Email: ")
            password = get_input("Password: ", is_password=True)
            phone = get_input("Phone: ")
            dob = get_input("DOB (YYYY-MM-DD): ")
            role = get_input("Role (POLICY_AGENT / CLAIM_OFFICER): ").upper()
            
            if role not in ['POLICY_AGENT', 'CLAIM_OFFICER']:
                print_error("Invalid role.")
                continue
                
            hashed_pw = hash_password(password)
            try:
                execute_query(
                    "INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, email, hashed_pw, phone, dob, role)
                )
                print_success(f"{role} added successfully.")
            except Exception as e:
                print_error(f"Failed to add agent: {e}")
        elif choice == 2:
            agents = fetch_all("SELECT user_id, full_name, email, role, is_active FROM users WHERE role IN ('POLICY_AGENT', 'CLAIM_OFFICER')")
            if not agents:
                print_info("No staff members found.")
            for a in agents:
                status_str = "Active" if a['is_active'] == 1 else "Inactive"
                print_card(f"STAFF #{a['user_id']} - {a['full_name']}", [
                    ("Email", a['email']),
                    ("Role", a['role']),
                    ("Status", status_str)
                ])
        elif choice == 3:
            u_id = get_input("Enter Agent/Officer User ID: ", cast_type=int)
            agent = fetch_one("SELECT * FROM users WHERE user_id = ? AND role IN ('POLICY_AGENT', 'CLAIM_OFFICER')", (u_id,))
            if not agent:
                print_error("Agent/Officer not found.")
                continue
                
            print("\n1. Update Phone Number")
            print("2. Toggle Active Status")
            print("0. Cancel")
            sub = get_input("Select option: ", cast_type=int)
            
            try:
                if sub == 1:
                    phone = get_input("New Phone: ")
                    execute_query("UPDATE users SET phone = ? WHERE user_id = ?", (phone, u_id))
                    print_success("Phone updated.")
                elif sub == 2:
                    new_status = 0 if agent['is_active'] == 1 else 1
                    execute_query("UPDATE users SET is_active = ? WHERE user_id = ?", (new_status, u_id))
                    print_success(f"Status toggled to {'Active' if new_status == 1 else 'Inactive'}.")
            except Exception as e:
                print_error(f"Failed to update agent: {e}")
        elif choice == 0:
            break

def admin_claim_management():
    while True:
        display_header("ADMIN CLAIM MANAGEMENT")
        print("1. View Unassigned Claim Pool")
        print("2. Assign Claim to Officer")
        print("3. View All Claims")
        print("4. Search Claim by ID")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            claims = fetch_all("SELECT * FROM claims WHERE status = 'PENDING_ASSIGNMENT'")
            if not claims:
                print_info("No unassigned claims in pool.")
            for c in claims:
                print_card(f"UNASSIGNED CLAIM #{c['claim_id']}", [
                    ("Customer ID", c['customer_id']),
                    ("Policy ID", c['customer_policy_id']),
                    ("Claim Amount", format_inr(c['claim_amount'])),
                    ("Claim Reason", c['claim_reason']),
                    ("Filed At", c['filed_at'])
                ])
        elif choice == 2:
            claim_id = get_input("Enter Claim ID: ", cast_type=int)
            officer_id = get_input("Enter Claim Officer ID: ", cast_type=int)
            try:
                execute_query("UPDATE claims SET claim_officer_id = ?, status = 'UNDER_REVIEW' WHERE claim_id = ?", (officer_id, claim_id))
                execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim_id, current_user['user_id'], 'ASSIGNED', 'Assigned by Admin'))
                print_success("Claim assigned successfully.")
            except Exception as e:
                print_error(f"Failed to assign claim: {e}")
        elif choice == 3:
            claims = fetch_all("SELECT * FROM claims")
            if not claims:
                print_info("No claims found.")
            for c in claims:
                print_card(f"CLAIM #{c['claim_id']}", [
                    ("Customer ID", c['customer_id']),
                    ("Claim Amount", format_inr(c['claim_amount'])),
                    ("Status", c['status']),
                    ("Assigned Officer ID", c['claim_officer_id'] or "Unassigned")
                ])
        elif choice == 4:
            claim_id = get_input("Enter Claim ID: ", cast_type=int)
            claim_row = fetch_one("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
            if claim_row:
                claim = dict(claim_row)
                print_card(f"CLAIM DETAILS #{claim['claim_id']}", [
                    ("Customer ID", claim['customer_id']),
                    ("Policy ID", claim['customer_policy_id']),
                    ("Claim Amount", format_inr(claim['claim_amount'])),
                    ("Claim Reason", claim['claim_reason']),
                    ("Additional Details", claim.get('additional_details') or "None"),
                    ("Status", claim['status']),
                    ("Assigned Officer ID", claim['claim_officer_id'] or "Unassigned"),
                    ("Officer Remarks", claim.get('officer_remarks') or "None"),
                    ("Filed At", claim['filed_at']),
                    ("Updated At", claim['updated_at'])
                ])
            else:
                print_error("Claim not found.")
        elif choice == 0:
            break

def admin_policy_management():
    while True:
        display_header("POLICY MANAGEMENT")
        print("1. View All Customer Policies")
        print("2. Search Policy by ID")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            policies = fetch_all("SELECT cp.*, mp.policy_name, u.email FROM customer_policies cp JOIN master_policies mp ON cp.policy_id = mp.policy_id JOIN users u ON cp.customer_id = u.user_id")
            if not policies:
                print_info("No policies found.")
            for p_row in policies:
                p = dict(p_row)
                print_card(f"CUSTOMER POLICY #{p['customer_policy_id']}", [
                    ("Customer Email", p['email']),
                    ("Policy Plan", p['policy_name']),
                    ("Status", p['status']),
                    ("Start Date", p.get('start_date') or "Pending"),
                    ("Expiry Date", p.get('expiry_date') or "Pending")
                ])
        elif choice == 2:
            cp_id = get_input("Enter Customer Policy ID: ", cast_type=int)
            policy_row = fetch_one("SELECT cp.*, mp.policy_name, u.email FROM customer_policies cp JOIN master_policies mp ON cp.policy_id = mp.policy_id JOIN users u ON cp.customer_id = u.user_id WHERE cp.customer_policy_id = ?", (cp_id,))
            if policy_row:
                policy = dict(policy_row)
                print_card(f"POLICY DETAILS #{policy['customer_policy_id']}", [
                    ("Customer Email", policy['email']),
                    ("Master Policy ID", policy['policy_id']),
                    ("Policy Name", policy['policy_name']),
                    ("Nominee Name", policy['nominee_name']),
                    ("Nominee Relation", policy['nominee_relation']),
                    ("Status", policy['status']),
                    ("Assigned Agent ID", policy['assigned_agent_id'] or "None"),
                    ("Agent Remarks", policy.get('agent_remarks') or "None"),
                    ("Start Date", policy.get('start_date') or "Pending"),
                    ("Expiry Date", policy.get('expiry_date') or "Pending"),
                    ("Created At", policy['created_at'])
                ])
            else:
                print_error("Policy not found.")
        elif choice == 0:
            break

def admin_reports():
    while True:
        display_header("SYSTEM REPORTS")
        print("1. Active Policies Report")
        print("2. Approved Claims Report")
        print("3. Expired Policies Report")
        print("4. Rejected Claims Report")
        print("5. Agent Performance Report")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            display_header("REPORT: ACTIVE POLICIES")
            policies = fetch_all("""
                SELECT cp.*, mp.policy_name, mp.premium_amount, mp.sum_insured, u.full_name as cust_name, u.email as cust_email, a.full_name as agent_name
                FROM customer_policies cp
                JOIN master_policies mp ON cp.policy_id = mp.policy_id
                JOIN users u ON cp.customer_id = u.user_id
                LEFT JOIN users a ON cp.assigned_agent_id = a.user_id
                WHERE cp.status = 'ACTIVE'
            """)
            print_info(f"Total Active Policies: {len(policies)}")
            for p_row in policies:
                p = dict(p_row)
                print_card(f"ACTIVE POLICY #{p['customer_policy_id']}", [
                    ("Customer Name", p['cust_name']),
                    ("Customer Email", p['cust_email']),
                    ("Plan Name", p['policy_name']),
                    ("Sum Insured", format_inr(p['sum_insured'])),
                    ("Annual Premium", format_inr(p['premium_amount'])),
                    ("Start Date", p.get('start_date') or "N/A"),
                    ("Expiry Date", p.get('expiry_date') or "N/A"),
                    ("Assigned Agent", p['agent_name'] or "Unassigned")
                ])
        elif choice == 2:
            display_header("REPORT: APPROVED CLAIMS")
            claims = fetch_all("""
                SELECT c.*, cp.customer_policy_id, mp.policy_name, u.full_name as cust_name, u.email as cust_email, o.full_name as officer_name
                FROM claims c
                JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id
                JOIN master_policies mp ON cp.policy_id = mp.policy_id
                JOIN users u ON c.customer_id = u.user_id
                LEFT JOIN users o ON c.claim_officer_id = o.user_id
                WHERE c.status = 'APPROVED'
            """)
            total_amt = sum(c['claim_amount'] for c in claims)
            print_info(f"Total Approved Claims: {len(claims)} | Total Disbursed: {format_inr(total_amt)}")
            for c_row in claims:
                c = dict(c_row)
                print_card(f"APPROVED CLAIM #{c['claim_id']}", [
                    ("Customer Name", c['cust_name']),
                    ("Customer Email", c['cust_email']),
                    ("Policy Plan", c['policy_name']),
                    ("Approved Amount", format_inr(c['claim_amount'])),
                    ("Claim Reason", c['claim_reason']),
                    ("Claim Officer", c['officer_name'] or "System Admin"),
                    ("Officer Remarks", c.get('officer_remarks') or "Approved"),
                    ("Filed At", c['filed_at'])
                ])
        elif choice == 3:
            display_header("REPORT: EXPIRED POLICIES")
            policies = fetch_all("""
                SELECT cp.*, mp.policy_name, mp.premium_amount, u.full_name as cust_name, u.email as cust_email
                FROM customer_policies cp
                JOIN master_policies mp ON cp.policy_id = mp.policy_id
                JOIN users u ON cp.customer_id = u.user_id
                WHERE cp.status = 'EXPIRED'
            """)
            print_info(f"Total Expired Policies: {len(policies)}")
            for p_row in policies:
                p = dict(p_row)
                print_card(f"EXPIRED POLICY #{p['customer_policy_id']}", [
                    ("Customer Name", p['cust_name']),
                    ("Customer Email", p['cust_email']),
                    ("Plan Name", p['policy_name']),
                    ("Annual Premium", format_inr(p['premium_amount'])),
                    ("Start Date", p.get('start_date') or "N/A"),
                    ("Expiry Date", p.get('expiry_date') or "N/A")
                ])
        elif choice == 4:
            display_header("REPORT: REJECTED CLAIMS")
            claims = fetch_all("""
                SELECT c.*, mp.policy_name, u.full_name as cust_name, u.email as cust_email, o.full_name as officer_name
                FROM claims c
                JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id
                JOIN master_policies mp ON cp.policy_id = mp.policy_id
                JOIN users u ON c.customer_id = u.user_id
                LEFT JOIN users o ON c.claim_officer_id = o.user_id
                WHERE c.status = 'REJECTED'
            """)
            total_amt = sum(c['claim_amount'] for c in claims)
            print_info(f"Total Rejected Claims: {len(claims)} | Total Rejected Amount: {format_inr(total_amt)}")
            if not claims:
                print_info("No rejected claims recorded.")
            for c_row in claims:
                c = dict(c_row)
                print_card(f"REJECTED CLAIM #{c['claim_id']}", [
                    ("Customer Name", c['cust_name']),
                    ("Customer Email", c['cust_email']),
                    ("Policy Plan", c['policy_name']),
                    ("Claimed Amount", format_inr(c['claim_amount'])),
                    ("Claim Reason", c['claim_reason']),
                    ("Reviewing Officer", c['officer_name'] or "System Admin"),
                    ("Rejection Reason", c.get('officer_remarks') or "None"),
                    ("Filed At", c['filed_at'])
                ])
        elif choice == 5:
            display_header("REPORT: AGENT & OFFICER PERFORMANCE")
            agents = fetch_all("""
                SELECT u.user_id, u.full_name, u.email, u.role,
                (SELECT COUNT(*) FROM customer_policies cp WHERE cp.assigned_agent_id = u.user_id AND cp.status = 'ACTIVE') as policies_approved,
                (SELECT COUNT(*) FROM customer_policies cp WHERE cp.assigned_agent_id = u.user_id AND cp.status = 'REJECTED') as policies_rejected,
                (SELECT COUNT(*) FROM claims c WHERE c.claim_officer_id = u.user_id AND c.status = 'APPROVED') as claims_approved,
                (SELECT COUNT(*) FROM claims c WHERE c.claim_officer_id = u.user_id AND c.status = 'REJECTED') as claims_rejected
                FROM users u WHERE u.role IN ('POLICY_AGENT', 'CLAIM_OFFICER')
            """)
            print_info(f"Total Staff Active: {len(agents)}")
            for a in agents:
                if a['role'] == 'POLICY_AGENT':
                    total_req = a['policies_approved'] + a['policies_rejected']
                    metrics = [
                        ("Staff Email", a['email']),
                        ("Role", "POLICY AGENT"),
                        ("Total Handled", total_req),
                        ("Policies Approved", a['policies_approved']),
                        ("Policies Rejected", a['policies_rejected'])
                    ]
                else:
                    total_claims = a['claims_approved'] + a['claims_rejected']
                    metrics = [
                        ("Staff Email", a['email']),
                        ("Role", "CLAIM OFFICER"),
                        ("Total Processed", total_claims),
                        ("Claims Approved", a['claims_approved']),
                        ("Claims Rejected", a['claims_rejected'])
                    ]
                print_card(f"STAFF #{a['user_id']} - {a['full_name']}", metrics)
        elif choice == 0:
            break

def admin_dashboard():
    global current_user
    while current_user:
        display_header("ADMIN DASHBOARD")
        print("1. User Management")
        print("2. Agent Management")
        print("3. Policy Management")
        print("4. Claim Management")
        print("5. Reports")
        print("0. Logout")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            admin_user_management()
        elif choice == 2:
            admin_agent_management()
        elif choice == 3:
            admin_policy_management()
        elif choice == 4:
            admin_claim_management()
        elif choice == 5:
            admin_reports()
        elif choice == 0:
            current_user = None
            break

# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------
def main():
    while True:
        display_header("HEALTH INSURANCE MANAGEMENT SYSTEM")
        print("1. Register")
        print("2. Login")
        print("3. Request Account Reactivation")
        print("0. Exit")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            register_user()
        elif choice == 2:
            if login_user():
                role = current_user['role']
                if role == 'CUSTOMER':
                    customer_dashboard()
                elif role == 'POLICY_AGENT':
                    agent_dashboard()
                elif role == 'CLAIM_OFFICER':
                    officer_dashboard()
                elif role == 'ADMIN':
                    admin_dashboard()
        elif choice == 3:
            request_reactivation()
        elif choice == 0:
            print_success("Thank you for using HIMS. Goodbye!")
            sys.exit(0)
        else:
            print_error("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\nExiting HIMS...")
        sys.exit(0)
