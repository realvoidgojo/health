import datetime
import random
from database import execute_query, hash_password, print_success, print_info, print_error, fetch_all
import init_db

def seed_data():
    print_info("Resetting and initializing base database...")
    init_db.init_db()  # This drops, creates, and seeds the default admin and master policies
    
    print_info("Inserting realistic sample data...")
    
    # 1. Create Agents & Officers
    agent1_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Rajesh Kumar", "rajesh.agent@hims.com", hash_password("pass123"), "+91 9876543210", "1985-06-15", "POLICY_AGENT", 1, 0)
    )
    agent2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Sneha Desai", "sneha.agent@hims.com", hash_password("pass123"), "+91 9876543211", "1990-02-20", "POLICY_AGENT", 1, 0)
    )
    
    officer1_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Amit Patel", "amit.officer@hims.com", hash_password("pass123"), "+91 9876543212", "1982-11-05", "CLAIM_OFFICER", 1, 0)
    )
    officer2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Priya Sharma", "priya.officer@hims.com", hash_password("pass123"), "+91 9876543213", "1988-08-30", "CLAIM_OFFICER", 1, 0)
    )

    # 2. Create Customers
    cust1_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Rahul Singh", "rahul.singh@gmail.com", hash_password("pass123"), "+91 9876543214", "1995-04-12", "CUSTOMER", agent1_id, 1, 0)
    )
    cust2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Anjali Gupta", "anjali.g@yahoo.com", hash_password("pass123"), "+91 9876543215", "1975-09-25", "CUSTOMER", agent2_id, 1, 0)
    )
    cust3_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Vikram Verma", "vikram.v@hotmail.com", hash_password("pass123"), "+91 9876543216", "2000-01-15", "CUSTOMER", agent1_id, 1, 0)
    )
    cust4_deleted_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Neha Reddy", "neha.r@gmail.com", hash_password("pass123"), "+91 9876543217", "1980-12-10", "CUSTOMER", agent2_id, 0, 1)
    )
    
    # Add a reactivation request for the deleted user
    execute_query("INSERT INTO reactivation_requests (user_id, status) VALUES (?, ?)", (cust4_deleted_id, 'PENDING'))

    # Fetch master policies
    policies = fetch_all("SELECT * FROM master_policies")
    ind_plan_id = next(p['policy_id'] for p in policies if p['category'] == 'Individual Plan')
    fam_plan_id = next(p['policy_id'] for p in policies if p['category'] == 'Family Floater Plan')
    sen_plan_id = next(p['policy_id'] for p in policies if p['category'] == 'Senior Citizen Plan')

    today = datetime.date.today()
    last_year = today.replace(year=today.year - 1)
    next_year = today.replace(year=today.year + 1)
    expired_date = today - datetime.timedelta(days=10)

    # 3. Create Customer Policies
    # Rahul has active individual plan
    alice_pol_id = execute_query(
        "INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, start_date, expiry_date, status, assigned_agent_id, agent_remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (cust1_id, ind_plan_id, "Kavita Singh", "Wife", last_year, next_year, 'ACTIVE', agent1_id, "Approved based on clean medical history.")
    )
    
    # Anjali has expired senior plan
    bob_pol_id = execute_query(
        "INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, start_date, expiry_date, status, assigned_agent_id, agent_remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (cust2_id, sen_plan_id, "Suresh Gupta", "Husband", last_year.replace(year=last_year.year - 1), today.replace(day=1), 'EXPIRED', agent2_id, "Standard approval.")
    )
    
    # Vikram has pending family plan request
    execute_query(
        "INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id) VALUES (?, ?, ?, ?, ?, ?)",
        (cust3_id, fam_plan_id, "Sunita Verma", "Mother", 'PENDING_APPROVAL', agent1_id)
    )
    
    # Anjali has rejected individual plan (agent suggested senior plan)
    execute_query(
        "INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id, suggested_policy_id, agent_remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (cust2_id, ind_plan_id, "Suresh Gupta", "Husband", 'REJECTED', agent2_id, sen_plan_id, "Customer age qualifies for Senior Citizen plan which has better benefits.")
    )

    # 4. Create Claims
    # Rahul: Approved claim
    claim1_id = execute_query(
        """INSERT INTO claims 
        (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (alice_pol_id, cust1_id, 15000.50, "Viral Fever Hospitalization (3 Days)", 'APPROVED', officer1_id, "All documents verified and valid.")
    )
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim1_id, officer1_id, 'ASSIGNED', 'Assigned by System Admin'))
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (claim1_id, officer1_id, 'APPROVED', 'All documents verified and valid.'))
    
    # Rahul: Pending assignment claim
    execute_query(
        """INSERT INTO claims 
        (customer_policy_id, customer_id, claim_amount, claim_reason, status) 
        VALUES (?, ?, ?, ?, ?)""",
        (alice_pol_id, cust1_id, 5000.00, "Dental Surgery", 'PENDING_ASSIGNMENT')
    )

    # Anjali: Claim Needs Update
    bob_claim_id = execute_query(
        """INSERT INTO claims 
        (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (bob_pol_id, cust2_id, 45000.00, "Knee Replacement Surgery", 'NEEDS_UPDATE', officer2_id, "Please upload the final discharge summary bill.")
    )
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (bob_claim_id, officer2_id, 'ASSIGNED', 'Assigned by System Admin'))
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (bob_claim_id, officer2_id, 'REQUESTED_UPDATE', 'Please upload the final discharge summary bill.'))

    # 5. Admin global assignment history (optional, simulating admin actions)
    # Using default admin user_id = 1
    execute_query("UPDATE claim_history SET officer_id = 1 WHERE action_taken = 'ASSIGNED'") 

    print_success("\n=======================================================")
    print_success("Database seeded successfully with rich, realistic data!")
    print_success("=======================================================")
    print_info("\nTry logging in with these test accounts (Password for all: 'pass123'):")
    print_info("- Admin:        admin@hims.com")
    print_info("- Policy Agent: rajesh.agent@hims.com")
    print_info("- Claim Officer:amit.officer@hims.com")
    print_info("- Customer:     rahul.singh@gmail.com")
    print_info("- Customer:     anjali.g@yahoo.com")
    print_info("- Customer:     neha.r@gmail.com (Soft Deleted - check Reactivation flow)")

if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print_error(f"Failed to seed data: {e}")
