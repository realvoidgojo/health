import sys
from datetime import datetime
from database import fetch_all, fetch_one, execute_query, hash_password, get_input, print_success, print_error, print_warning, print_info, Colors

current_user = None

def display_header(title):
    print(f"\n{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.CYAN}{title.center(50)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
def register_user():
    display_header("REGISTER NEW ACCOUNT")
    name = get_input("Full Name: ")
    email = get_input("Email Address: ")
    password = get_input("Password: ")
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
    password = get_input("Password: ")
    
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
    password = get_input("Password: ")
    
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
            print(f"\nName: {current_user['full_name']}")
            print(f"Email: {current_user['email']}")
            print(f"Phone: {current_user['phone']}")
            print(f"DOB: {current_user['date_of_birth']}")
        elif choice == 2:
            phone = get_input("New Phone Number: ")
            try:
                execute_query("UPDATE users SET phone = ? WHERE user_id = ?", (phone, current_user['user_id']))
                current_user['phone'] = phone
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
        print("4. Update Nominee")
        print("5. Renew Policy")
        print("6. Cancel Policy")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            policies = fetch_all("SELECT * FROM master_policies WHERE is_active = 1")
            for p in policies:
                print(f"ID: {p['policy_id']} | Name: {p['policy_name']} | Category: {p['category']}")
                print(f"Sum Insured: {p['sum_insured']} | Premium: {p['premium_amount']}")
                print(f"Details: {p['coverage_details']}\n")
        elif choice == 2:
            policy_id = get_input("Enter Policy ID to purchase: ", cast_type=int)
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
            for p in policies:
                print(f"Customer Policy ID: {p['customer_policy_id']} | Policy Name: {p['policy_name']} | Status: {p['status']}")
                print(f"Nominee: {p['nominee_name']} | Agent Remarks: {p['agent_remarks']}\n")
                if p['suggested_policy_id']:
                    print_info(f"Agent suggested alternative Policy ID: {p['suggested_policy_id']}")
        elif choice == 4:
            cp_id = get_input("Enter Customer Policy ID: ", cast_type=int)
            new_nominee = get_input("New Nominee Name: ")
            try:
                execute_query("UPDATE customer_policies SET nominee_name = ? WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'", (new_nominee, cp_id, current_user['user_id']))
                print_success("Nominee updated.")
            except Exception as e:
                print_error(f"Failed to update nominee: {e}")
        elif choice == 5:
            cp_id = get_input("Enter Customer Policy ID to renew: ", cast_type=int)
            try:
                execute_query("UPDATE customer_policies SET status = 'ACTIVE' WHERE customer_policy_id = ? AND customer_id = ?", (cp_id, current_user['user_id']))
                print_success("Policy renewed.")
            except Exception as e:
                print_error(f"Failed to renew policy: {e}")
        elif choice == 6:
            cp_id = get_input("Enter Customer Policy ID to cancel: ", cast_type=int)
            try:
                execute_query("UPDATE customer_policies SET status = 'CANCELLED' WHERE customer_policy_id = ? AND customer_id = ? AND status = 'ACTIVE'", (cp_id, current_user['user_id']))
                print_success("Policy cancelled.")
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
            for c in claims:
                print(f"Claim ID: {c['claim_id']} | Amount: {c['claim_amount']} | Status: {c['status']}")
                print(f"Reason: {c['claim_reason']} | Remarks: {c['officer_remarks']}\n")
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
                
                # We should log to claim history that customer updated, but usually officer logs it. We can add a generic log here if needed.
                execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim_id, 1, 'CUSTOMER_UPDATED', 'Customer updated claim details')) # Using admin (1) as system proxy
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
            for c in customers:
                print(f"ID: {c['user_id']} | Name: {c['full_name']} | Email: {c['email']}")
        elif choice == 2:
            policies = fetch_all("SELECT cp.*, u.full_name FROM customer_policies cp JOIN users u ON cp.customer_id = u.user_id WHERE cp.assigned_agent_id = ?", (current_user['user_id'],))
            for p in policies:
                print(f"Customer Policy ID: {p['customer_policy_id']} | Customer: {p['full_name']} | Status: {p['status']}")
        elif choice == 3:
            requests = fetch_all("SELECT cp.*, u.full_name FROM customer_policies cp JOIN users u ON cp.customer_id = u.user_id WHERE cp.assigned_agent_id = ? AND cp.status = 'PENDING_APPROVAL'", (current_user['user_id'],))
            if not requests:
                print_info("No pending policy requests.")
                continue
            for r in requests:
                print(f"Request ID: {r['customer_policy_id']} | Customer: {r['full_name']} | Policy ID: {r['policy_id']}")
                
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
                print(f"Claim ID: {c['claim_id']} | Amount: {c['claim_amount']} | Reason: {c['claim_reason']}")
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
            for log in logs:
                print(f"Log ID: {log['history_id']} | Claim ID: {log['claim_id']} | Action: {log['action_taken']} | Time: {log['action_timestamp']}")
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
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            users = fetch_all("SELECT user_id, full_name, email, role, is_active, is_deleted FROM users")
            for u in users:
                print(dict(u))
        elif choice == 2:
            email = get_input("Enter Email: ")
            user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
            if user:
                print(dict(user))
            else:
                print_error("User not found.")
        elif choice == 3:
            requests = fetch_all("SELECT r.*, u.email FROM reactivation_requests r JOIN users u ON r.user_id = u.user_id WHERE r.status = 'PENDING'")
            if not requests:
                print_info("No pending requests.")
                continue
            for r in requests:
                print(f"Request ID: {r['request_id']} | User: {r['email']} | Date: {r['request_date']}")
            req_id = get_input("Enter Request ID to approve (0 to cancel): ", cast_type=int)
            if req_id != 0:
                req = fetch_one("SELECT * FROM reactivation_requests WHERE request_id = ?", (req_id,))
                if req:
                    execute_query("UPDATE users SET is_deleted = 0, is_active = 1 WHERE user_id = ?", (req['user_id'],))
                    execute_query("UPDATE reactivation_requests SET status = 'APPROVED' WHERE request_id = ?", (req_id,))
                    print_success("User account reactivated.")
        elif choice == 0:
            break

def admin_agent_management():
    while True:
        display_header("AGENT MANAGEMENT")
        print("1. Add Policy Agent / Claim Officer")
        print("2. View All Agents/Officers")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            name = get_input("Full Name: ")
            email = get_input("Email: ")
            password = get_input("Password: ")
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
            agents = fetch_all("SELECT user_id, full_name, email, role FROM users WHERE role IN ('POLICY_AGENT', 'CLAIM_OFFICER')")
            for a in agents:
                print(dict(a))
        elif choice == 0:
            break

def admin_claim_management():
    while True:
        display_header("ADMIN CLAIM MANAGEMENT")
        print("1. View Unassigned Claim Pool")
        print("2. Assign Claim to Officer")
        print("3. View All Claims")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            claims = fetch_all("SELECT * FROM claims WHERE status = 'PENDING_ASSIGNMENT'")
            for c in claims:
                print(dict(c))
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
            for c in claims:
                print(f"Claim ID: {c['claim_id']} | Status: {c['status']} | Officer ID: {c['claim_officer_id']}")
        elif choice == 0:
            break

def admin_reports():
    while True:
        display_header("SYSTEM REPORTS")
        print("1. Active Policies Report")
        print("2. Approved Claims Report")
        print("0. Back")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            count = fetch_one("SELECT COUNT(*) as c FROM customer_policies WHERE status = 'ACTIVE'")['c']
            print_info(f"Total Active Policies: {count}")
        elif choice == 2:
            count = fetch_one("SELECT COUNT(*) as c FROM claims WHERE status = 'APPROVED'")['c']
            print_info(f"Total Approved Claims: {count}")
        elif choice == 0:
            break

def admin_dashboard():
    global current_user
    while current_user:
        display_header("ADMIN DASHBOARD")
        print("1. User Management")
        print("2. Agent Management")
        print("3. Claim Management")
        print("4. Reports")
        print("0. Logout")
        choice = get_input("Select an option: ", cast_type=int)
        
        if choice == 1:
            admin_user_management()
        elif choice == 2:
            admin_agent_management()
        elif choice == 3:
            admin_claim_management()
        elif choice == 4:
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
