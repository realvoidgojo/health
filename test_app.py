import unittest
import sqlite3
import database
import init_db
import main
from unittest.mock import patch
from contextlib import contextmanager

class TestHIMSApp(unittest.TestCase):
    
    def setUp(self):
        # Create a new in-memory connection for this test
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        
        # Patch the context manager to yield our persistent in-memory connection
        @contextmanager
        def mock_get_db_connection(db_path=None):
            try:
                self.conn.execute("PRAGMA foreign_keys = ON;")
                yield self.conn
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise e
                
        self.patcher = patch('database.get_db_connection', mock_get_db_connection)
        self.patcher.start()
        
        # Rebuild schema and seed data in memory
        sql_script = init_db.SCHEMA_SQL
        hashed_admin_pw = database.hash_password("admin123")
        sql_script = sql_script.replace("{admin_pw_placeholder}", hashed_admin_pw)
        self.conn.executescript(sql_script)
        self.conn.commit()
        
    def tearDown(self):
        self.patcher.stop()
        self.conn.close()

    def test_user_registration_and_duplicate_email(self):
        # 1. Registration
        with patch('builtins.input', side_effect=['Test User', 'test@example.com', 'pass123', '1234567890', '1990-01-01']):
            main.register_user()
            
        user = database.fetch_one("SELECT * FROM users WHERE email = 'test@example.com'")
        self.assertIsNotNone(user)
        self.assertEqual(user['full_name'], 'Test User')
        
        # 2. Duplicate Email Registration
        with patch('builtins.input', side_effect=['Test User 2', 'test@example.com', 'pass123', '0987654321', '1991-01-01']):
            with patch('main.print_error') as mock_error:
                main.register_user()
                mock_error.assert_called_with("An account with this email already exists.")

    def test_authentication_logic(self):
        # Register user first
        database.execute_query(
            "INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('Auth User', 'auth@example.com', database.hash_password('mypass'), '111', '2000-01-01', 'CUSTOMER', 1, 0)
        )
        
        # 1. Valid Credentials
        with patch('builtins.input', side_effect=['auth@example.com', 'mypass']):
            result = main.login_user()
            self.assertTrue(result)
            self.assertEqual(main.current_user['email'], 'auth@example.com')
            
        main.current_user = None
        
        # 2. Invalid Password
        with patch('builtins.input', side_effect=['auth@example.com', 'wrongpass']):
            with patch('main.print_error') as mock_error:
                result = main.login_user()
                self.assertFalse(result)
                mock_error.assert_called_with("Invalid email or password.")
                
        # 3. Soft-deleted User Block
        database.execute_query("UPDATE users SET is_deleted = 1, is_active = 0 WHERE email = 'auth@example.com'")
        with patch('builtins.input', side_effect=['auth@example.com', 'mypass']):
            with patch('main.print_error') as mock_error:
                result = main.login_user()
                self.assertFalse(result)
                mock_error.assert_called_with("This account has been deleted. Please request reactivation.")

    def test_policy_purchase_flow(self):
        main.current_user = {
            'user_id': 2, # Assuming admin is 1, let's hardcode this
            'assigned_agent_id': None
        }
        # Insert a customer
        database.execute_query("INSERT INTO users (user_id, full_name, email, password, phone, date_of_birth, role) VALUES (2, 'Cust', 'c@c.com', 'pw', '12', '1990', 'CUSTOMER')")
        
        with patch('builtins.input', side_effect=[1, 'Nominee', 'Brother']):
            # Purchase policy ID 1
            with patch('builtins.input', side_effect=['2', '1', 'Nominee', 'Brother', '0']): # using menu option 2 then back
                main.customer_policy_menu()
                
        # Check PENDING_APPROVAL
        pol = database.fetch_one("SELECT status FROM customer_policies WHERE customer_id = 2")
        self.assertIsNotNone(pol)
        self.assertEqual(pol['status'], 'PENDING_APPROVAL')

    def test_agent_policy_approval_and_rejection(self):
        # Set up a customer and an agent
        database.execute_query("INSERT INTO users (user_id, full_name, email, password, phone, date_of_birth, role) VALUES (2, 'Agent', 'a@a.com', 'pw', '12', '1990', 'POLICY_AGENT')")
        database.execute_query("INSERT INTO users (user_id, full_name, email, password, phone, date_of_birth, role, assigned_agent_id) VALUES (3, 'Cust', 'c@c.com', 'pw', '12', '1990', 'CUSTOMER', 2)")
        
        # Create a pending policy purchase
        cp_id = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id) VALUES (3, 1, 'Nom', 'Sis', 2)")
        
        main.current_user = {'user_id': 2, 'role': 'POLICY_AGENT'}
        
        # Approve
        with patch('builtins.input', side_effect=['3', str(cp_id), 'A', '0']): # Option 3 -> Request ID -> Approve -> Back (0)
            main.agent_dashboard()
        
        pol = database.fetch_one("SELECT status FROM customer_policies WHERE customer_policy_id = ?", (cp_id,))
        self.assertEqual(pol['status'], 'ACTIVE')
        
        # Reject and suggest alternative
        cp_id2 = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id) VALUES (3, 2, 'Nom', 'Sis', 2)")
        
        main.current_user = {'user_id': 2, 'role': 'POLICY_AGENT'}
        with patch('builtins.input', side_effect=['3', str(cp_id2), 'R', '3', 'Too expensive', '0']): 
            # Reject -> suggest policy 3 -> remarks -> Back (0)
            main.agent_dashboard()
            
        pol2 = database.fetch_one("SELECT status, suggested_policy_id FROM customer_policies WHERE customer_policy_id = ?", (cp_id2,))
        self.assertEqual(pol2['status'], 'REJECTED')
        self.assertEqual(pol2['suggested_policy_id'], 3)

    def test_claim_creation_and_status_transitions(self):
        # 1. Customer files claim
        database.execute_query("INSERT INTO users (user_id, full_name, email, password, phone, date_of_birth, role) VALUES (10, 'Cust', 'cc@c.com', 'pw', '12', '1990', 'CUSTOMER')")
        database.execute_query("INSERT INTO customer_policies (customer_policy_id, customer_id, policy_id, nominee_name, nominee_relation, status) VALUES (5, 10, 1, 'Nom', 'Sis', 'ACTIVE')")
        
        main.current_user = {'user_id': 10}
        with patch('builtins.input', side_effect=['1', '5', '1000.50', 'Fever', '0']): # Option 1 -> CP ID 5 -> amount -> reason -> back
            main.customer_claim_menu()
            
        claim = database.fetch_one("SELECT * FROM claims WHERE customer_policy_id = 5")
        self.assertEqual(claim['status'], 'PENDING_ASSIGNMENT')
        claim_id = claim['claim_id']
        
        # 2. Admin assigns claim
        main.current_user = {'user_id': 1} # Admin
        with patch('builtins.input', side_effect=['2', str(claim_id), '1', '0']): # Assign to officer 1
            main.admin_claim_management()
            
        claim = database.fetch_one("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
        self.assertEqual(claim['status'], 'UNDER_REVIEW')
        
        # 3. Officer reviews claim (needs update)
        main.current_user = {'user_id': 1, 'role': 'CLAIM_OFFICER'} # We assigned to ID 1
        with patch('builtins.input', side_effect=['2', str(claim_id), 'U', 'Need bills', '0']):
            main.officer_dashboard()
            
        claim = database.fetch_one("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
        self.assertEqual(claim['status'], 'NEEDS_UPDATE')
        
        # 4. Officer approves claim (assuming customer updated it, but let's test straight approve)
        main.current_user = {'user_id': 1, 'role': 'CLAIM_OFFICER'}
        with patch('builtins.input', side_effect=['2', str(claim_id), 'A', 'Looks good', '0']):
            main.officer_dashboard()
            
        claim = database.fetch_one("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
        self.assertEqual(claim['status'], 'APPROVED')

    def test_account_soft_delete_and_admin_reactivation(self):
        # Register user
        user_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role, is_active, is_deleted) VALUES ('Del', 'del@c.com', 'pw', '12', '1990', 'CUSTOMER', 1, 0)")
        
        # Delete via customer menu
        main.current_user = {'user_id': user_id, 'full_name': 'Del'}
        with patch('builtins.input', side_effect=['3', 'Y']): # Option 3: Delete, Y: Confirm
            main.customer_profile_menu()
            
        user = database.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        self.assertEqual(user['is_deleted'], 1)
        self.assertEqual(user['is_active'], 0)
        self.assertIsNone(main.current_user)
        
        # Request Reactivation
        with patch('builtins.input', side_effect=['del@c.com', 'pw']):
            # Need to mock hash_password since 'pw' will not match without hash, wait I inserted plain 'pw', let's use hash
            database.execute_query("UPDATE users SET password = ? WHERE user_id = ?", (database.hash_password('pw'), user_id))
            main.request_reactivation()
            
        req = database.fetch_one("SELECT * FROM reactivation_requests WHERE user_id = ?", (user_id,))
        self.assertEqual(req['status'], 'PENDING')
        req_id = req['request_id']
        
        # Admin approves
        with patch('builtins.input', side_effect=['3', str(req_id), 'A', 'Approved', '0']):
            main.admin_user_management()
            
        user = database.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        self.assertEqual(user['is_deleted'], 0)
        self.assertEqual(user['is_active'], 1)

    def test_admin_system_reports_all_options(self):
        # Insert sample active policy, approved claim, expired policy, rejected claim
        cust_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Report Cust', 'rep@c.com', 'pw', '123', '1990', 'CUSTOMER')")
        officer_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Report Officer', 'off@c.com', 'pw', '123', '1990', 'CLAIM_OFFICER')")
        agent_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Report Agent', 'ag@c.com', 'pw', '123', '1990', 'POLICY_AGENT')")

        cp_active = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status, assigned_agent_id) VALUES (?, 1, 'Nom', 'Sis', 'ACTIVE', ?)", (cust_id, agent_id))
        cp_expired = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status) VALUES (?, 1, 'Nom', 'Sis', 'EXPIRED')", (cust_id,))

        database.execute_query("INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) VALUES (?, ?, 5000, 'Fever', 'APPROVED', ?, 'Approved ok')", (cp_active, cust_id, officer_id))
        database.execute_query("INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason, status, claim_officer_id, officer_remarks) VALUES (?, ?, 10000, 'Accident', 'REJECTED', ?, 'Not covered')", (cp_active, cust_id, officer_id))

        # Test options 1, 2, 3, 4, 5, 0 sequentially in admin_reports()
        with patch('builtins.input', side_effect=['1', '2', '3', '4', '5', '0']):
            main.admin_reports()

    def test_admin_policy_management(self):
        cust_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Pol Cust', 'pol@c.com', 'pw', '123', '1990', 'CUSTOMER')")
        cp_id = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status) VALUES (?, 1, 'Nom', 'Sis', 'ACTIVE')", (cust_id,))

        # Test choice 1 (View All), choice 2 (Search by ID), choice 0 (Back)
        with patch('builtins.input', side_effect=['1', '2', str(cp_id), '0']):
            main.admin_policy_management()

    def test_admin_claim_management_extended(self):
        cust_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Claim Cust', 'cl@c.com', 'pw', '123', '1990', 'CUSTOMER')")
        cp_id = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status) VALUES (?, 1, 'Nom', 'Sis', 'ACTIVE')", (cust_id,))
        claim_id = database.execute_query("INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason, status) VALUES (?, ?, 2000, 'Checkup', 'PENDING_ASSIGNMENT')", (cp_id, cust_id))

        # Test choice 1 (Unassigned Pool), choice 3 (View All Claims), choice 4 (Search Claim by ID), choice 0 (Back)
        with patch('builtins.input', side_effect=['1', '3', '4', str(claim_id), '0']):
            main.admin_claim_management()

    def test_admin_agent_management_extended(self):
        # 1. Add Agent (choice 1)
        with patch('builtins.input', side_effect=['1', 'New Staff', 'staff@hims.com', 'pass123', '999', '1990-01-01', 'POLICY_AGENT', '0']):
            main.admin_agent_management()

        staff = database.fetch_one("SELECT * FROM users WHERE email = 'staff@hims.com'")
        self.assertIsNotNone(staff)
        staff_id = staff['user_id']

        # 2. View All Staff (choice 2) & Edit Staff Phone/Status (choice 3)
        with patch('builtins.input', side_effect=['2', '3', str(staff_id), '1', '888888', '3', str(staff_id), '2', '0']):
            main.admin_agent_management()

        updated_staff = database.fetch_one("SELECT * FROM users WHERE user_id = ?", (staff_id,))
        self.assertEqual(updated_staff['phone'], '888888')
        self.assertEqual(updated_staff['is_active'], 0)

    def test_customer_extended_flows(self):
        cust_id = database.execute_query("INSERT INTO users (full_name, email, password, phone, date_of_birth, role) VALUES ('Flow Cust', 'flow@c.com', 'pw', '123', '1990-01-01', 'CUSTOMER')")
        main.current_user = dict(database.fetch_one("SELECT * FROM users WHERE user_id = ?", (cust_id,)))

        # 1. Profile View (1) and Profile Edit (2 -> update phone)
        with patch('builtins.input', side_effect=['1', '2', '2', '777777', '0']):
            main.customer_profile_menu()

        self.assertEqual(main.current_user['phone'], '777777')

        # 2. Policy Menu: View Available (1), View My (3), View Suggested (4), Update Nominee (5)
        cp_id = database.execute_query("INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, status) VALUES (?, 1, 'OldNom', 'Bro', 'ACTIVE')", (cust_id,))
        with patch('builtins.input', side_effect=['1', '3', '4', '5', str(cp_id), 'NewNom', 'Sister', '0']):
            main.customer_policy_menu()

        cp = database.fetch_one("SELECT * FROM customer_policies WHERE customer_policy_id = ?", (cp_id,))
        self.assertEqual(cp['nominee_name'], 'NewNom')
        self.assertEqual(cp['nominee_relation'], 'Sister')

if __name__ == '__main__':
    unittest.main()
