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
        ("Sarah Agent", "sarah.agent@hims.com", hash_password("pass123"), "555-0101", "1985-06-15", "POLICY_AGENT", 1, 0)
    )
    agent2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Michael Consultant", "michael.c@hims.com", hash_password("pass123"), "555-0102", "1990-02-20", "POLICY_AGENT", 1, 0)
    )
    
    officer1_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("David Officer", "david.o@hims.com", hash_password("pass123"), "555-0201", "1982-11-05", "CLAIM_OFFICER", 1, 0)
    )
    officer2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("Elena Reviewer", "elena.r@hims.com", hash_password("pass123"), "555-0202", "1988-08-30", "CLAIM_OFFICER", 1, 0)
    )

    # 2. Create Customers
    cust1_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Alice Johnson", "alice@gmail.com", hash_password("pass123"), "555-0301", "1995-04-12", "CUSTOMER", agent1_id, 1, 0)
    )
    cust2_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Bob Smith", "bob.smith@yahoo.com", hash_password("pass123"), "555-0302", "1975-09-25", "CUSTOMER", agent2_id, 1, 0)
    )
    cust3_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Charlie Brown", "charlie@hotmail.com", hash_password("pass123"), "555-0303", "2000-01-15", "CUSTOMER", agent1_id, 1, 0)
    )
    cust4_deleted_id = execute_query(
        "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Diana Prince", "diana.p@gmail.com", hash_password("pass123"), "555-0304", "1980-12-10", "CUSTOMER", agent2_id, 0, 1)
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
    # Alice: Active Individual Plan
    alice_pol_id = execute_query(
        """INSERT INTO customer_policies 
        (customer_id, policy_id, nominee_name, nominee_relation, start_date, expiry_date, status, assigned_agent_id, agent_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cust1_id, ind_plan_id, "Mark Johnson", "Husband", str(last_year), str(next_year), 'ACTIVE', agent1_id, "Approved based on clean medical history.")
    )
    
    # Bob: Expired Senior Plan
    bob_pol_id = execute_query(
        """INSERT INTO customer_policies 
        (customer_id, policy_id, nominee_name, nominee_relation, start_date, expiry_date, status, assigned_agent_id, agent_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cust2_id, sen_plan_id, "Mary Smith", "Wife", str(last_year.replace(year=last_year.year - 1)), str(expired_date), 'EXPIRED', agent2_id, "Standard approval.")
    )
    
    # Charlie: Pending Family Plan
    execute_query(
        """INSERT INTO customer_policies 
        (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id) 
        VALUES (?, ?, ?, ?, ?, ?)""",
        (cust3_id, fam_plan_id, "Lucy Brown", "Mother", 'PENDING_APPROVAL', agent1_id)
    )
    
    # Bob: Rejected Individual Plan (with suggestion)
    execute_query(
        """INSERT INTO customer_policies 
        (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id, suggested_policy_id, agent_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (cust2_id, ind_plan_id, "Mary Smith", "Wife", 'REJECTED', agent2_id, sen_plan_id, "Customer age qualifies for Senior Citizen plan which has better benefits.")
    )

    # 4. Create Claims
    # Alice: Approved claim
    alice_claim_id = execute_query(
        """INSERT INTO claims 
        (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (alice_pol_id, cust1_id, 15000.50, "Viral Fever Hospitalization (3 Days)", 'APPROVED', officer1_id, "All documents verified and valid.")
    )
    # Alice claim history
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (alice_claim_id, officer1_id, 'ASSIGNED', 'Assigned by System Admin'))
    execute_query("INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)", (alice_claim_id, officer1_id, 'APPROVED', 'All documents verified and valid.'))

    # Alice: Pending assignment claim
    execute_query(
        """INSERT INTO claims 
        (customer_policy_id, customer_id, claim_amount, claim_reason, status) 
        VALUES (?, ?, ?, ?, ?)""",
        (alice_pol_id, cust1_id, 5000.00, "Dental Surgery", 'PENDING_ASSIGNMENT')
    )

    # Bob: Claim Needs Update
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
    print_info("- Policy Agent: sarah.agent@hims.com")
    print_info("- Claim Officer:david.o@hims.com")
    print_info("- Customer:     alice@gmail.com")
    print_info("- Customer:     bob.smith@yahoo.com")
    print_info("- Customer:     diana.p@gmail.com (Soft Deleted - check Reactivation flow)")

if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print_error(f"Failed to seed data: {e}")
