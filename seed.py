import init_db
from app.core.db.base_repository import execute_query, fetch_all, fetch_one
from app.core.security import hash_password
import random
from datetime import datetime, timedelta

def create_seed_data():
    print("Seeding professional Indian data...")
    # Admin is already seeded by init_db (ID 1)
    
    hashed_pw = hash_password("pass123")
    
    # --- 1. Seed Agents ---
    agents = [
        ("Rajesh Kumar", "rajesh.agent@hims.com", "+91 9876543210", "1985-06-15", "POLICY_AGENT"),
        ("Sneha Desai", "sneha.agent@hims.com", "+91 9876543211", "1990-02-20", "POLICY_AGENT"),
        ("Vikram Singh", "vikram.agent@hims.com", "+91 9876543212", "1982-11-05", "POLICY_AGENT"),
    ]
    
    agent_ids = []
    for a in agents:
        aid = execute_query(
            "INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES (?, ?, ?, ?, ?, ?)",
            (a[0], a[1], hashed_pw, a[2], a[3], a[4])
        )
        agent_ids.append(aid)

    # --- 2. Seed Claim Officers ---
    officers = [
        ("Amit Patel", "amit.officer@hims.com", "+91 9876543213", "1988-08-30", "CLAIM_OFFICER"),
        ("Priya Sharma", "priya.officer@hims.com", "+91 9876543214", "1992-04-12", "CLAIM_OFFICER"),
    ]
    
    officer_ids = []
    for o in officers:
        oid = execute_query(
            "INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES (?, ?, ?, ?, ?, ?)",
            (o[0], o[1], hashed_pw, o[2], o[3], o[4])
        )
        officer_ids.append(oid)

    # --- 3. Seed Customers ---
    customers = [
        ("Rahul Verma", "rahul.v@gmail.com", "+91 9876543215", "1995-04-12", "CUSTOMER", agent_ids[0]),
        ("Anjali Gupta", "anjali.g@yahoo.com", "+91 9876543216", "1975-09-25", "CUSTOMER", agent_ids[1]),
        ("Neha Reddy", "neha.r@gmail.com", "+91 9876543217", "1980-12-10", "CUSTOMER", agent_ids[2]),
        ("Arjun Nair", "arjun.nair@hotmail.com", "+91 9876543218", "1998-01-15", "CUSTOMER", agent_ids[0]),
        ("Pooja Iyer", "pooja.iyer@outlook.com", "+91 9876543219", "1989-11-22", "CUSTOMER", agent_ids[1]),
        ("Deleted User", "del.user@gmail.com", "+91 9876543220", "1990-01-01", "CUSTOMER", None)
    ]
    
    customer_ids = []
    for c in customers:
        cid = execute_query(
            "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (c[0], c[1], hashed_pw, c[2], c[3], c[4], c[5])
        )
        customer_ids.append(cid)
        
    # Mark last customer as deleted to test reactivation flows
    execute_query("UPDATE users SET is_deleted = 1, is_active = 0 WHERE user_id = ?", (customer_ids[-1],))
    execute_query("INSERT INTO reactivation_requests (user_id, status) VALUES (?, 'PENDING')", (customer_ids[-1],))

    # --- 4. Seed Customer Policies ---
    # Master policies: 1 (Individual, 5L, 7.2k), 2 (Family, 10L, 18k), 3 (Senior, 5L, 24k)
    now = datetime.now()
    
    cp_list = [
        # Active policies
        (customer_ids[0], 1, "Kavita Verma", "Wife", "ACTIVE", agent_ids[0], now - timedelta(days=100), now + timedelta(days=265)),
        (customer_ids[1], 3, "Suresh Gupta", "Husband", "ACTIVE", agent_ids[1], now - timedelta(days=200), now + timedelta(days=165)),
        # Expired policy
        (customer_ids[2], 1, "Karthik Reddy", "Husband", "EXPIRED", agent_ids[2], now - timedelta(days=400), now - timedelta(days=35)),
        # Pending policy
        (customer_ids[3], 2, "Anita Nair", "Mother", "PENDING_APPROVAL", agent_ids[0], None, None),
        # Rejected policy
        (customer_ids[4], 1, "Ramesh Iyer", "Father", "REJECTED", agent_ids[1], None, None)
    ]
    
    cp_ids = []
    for cp in cp_list:
        start_date = cp[6].strftime('%Y-%m-%d') if cp[6] else None
        expiry_date = cp[7].strftime('%Y-%m-%d') if cp[7] else None
        
        cpid = execute_query(
            """INSERT INTO customer_policies 
            (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id, start_date, expiry_date, agent_remarks) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cp[0], cp[1], cp[2], cp[3], cp[4], cp[5], start_date, expiry_date, 
             "Approved standard." if cp[4] == "ACTIVE" else "Pending documents." if cp[4] == "PENDING_APPROVAL" else "Age criteria not met.")
        )
        cp_ids.append(cpid)
        
    # --- 5. Seed Claims ---
    claims_list = [
        # Approved Claim
        (cp_ids[0], customer_ids[0], 15000.50, "Viral Fever Hospitalization (3 Days)", "APPROVED", officer_ids[0], "All documents verified and valid."),
        # Needs Update Claim
        (cp_ids[1], customer_ids[1], 45000.00, "Knee Replacement Surgery", "NEEDS_UPDATE", officer_ids[1], "Please upload the final discharge summary bill."),
        # Pending Assignment Claim
        (cp_ids[0], customer_ids[0], 5000.00, "Dental Surgery", "PENDING_ASSIGNMENT", None, None),
        # Rejected Claim
        (cp_ids[2], customer_ids[2], 12000.00, "Accident", "REJECTED", officer_ids[0], "Policy was expired at the time of the incident.")
    ]
    
    for cl in claims_list:
        claim_id = execute_query(
            """INSERT INTO claims 
            (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (cl[0], cl[1], cl[2], cl[3], cl[4], cl[5], cl[6])
        )
        
        if cl[5] is not None:
            # Add history
            execute_query(
                "INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)",
                (claim_id, 1, "ASSIGNED", "Assigned by System Admin") # System Admin assigned it
            )
            
            if cl[4] == "APPROVED":
                execute_query(
                    "INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)",
                    (claim_id, cl[5], "APPROVED", cl[6])
                )
            elif cl[4] == "NEEDS_UPDATE":
                execute_query(
                    "INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)",
                    (claim_id, cl[5], "REQUESTED_UPDATE", cl[6])
                )
            elif cl[4] == "REJECTED":
                execute_query(
                    "INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)",
                    (claim_id, cl[5], "REJECTED", cl[6])
                )

if __name__ == "__main__":
    init_db.init_db()
    create_seed_data()
    print("Seeding complete! You can now log in with the new credentials.")
