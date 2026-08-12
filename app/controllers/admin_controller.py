from app.services.admin_service import AdminService
from app.views.console.ui import display_header, get_input, print_success, print_error, print_info, print_card
from app.views.console.menus import Menus
from app.core.formatting import format_inr
from app.core.exceptions import AppError
from app.core.constants import Role

class AdminController:
    @staticmethod
    def dashboard(user: dict):
        while True:
            display_header("SYSTEM ADMIN DASHBOARD")
            print("1. User Management")
            print("2. Staff & Agent Management")
            print("3. Claim Management")
            print("4. Policy Management")
            print("5. System Reports")
            print("0. Logout")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                print_success("Logging out...")
                break
                
            if choice == 1:
                AdminController.user_management(user)
            elif choice == 2:
                AdminController.agent_management(user)
            elif choice == 3:
                AdminController.claim_management(user)
            elif choice == 4:
                AdminController.policy_management(user)
            elif choice == 5:
                AdminController.reports(user)
            else:
                print_error("Invalid option.")

    @staticmethod
    def user_management(user: dict):
        while True:
            display_header("USER MANAGEMENT")
            print("1. View All Users")
            print("2. Search by Email")
            print("3. View Reactivation Requests")
            print("4. Assign/Reassign Policy Agent")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                users = AdminService.get_all_users()
                Menus.print_users(users)
            elif choice == 2:
                email = get_input("Enter Email: ")
                u = AdminService.search_user_by_email(email)
                if u:
                    Menus.print_users([u])
                else:
                    print_error("User not found.")
            elif choice == 3:
                reqs = AdminService.get_pending_reactivations()
                if not reqs:
                    print_info("No pending reactivation requests.")
                    continue
                    
                Menus.print_reactivation_requests(reqs)
                
                req_id = get_input(
                    "Enter Request ID to process (0 to cancel): ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_reactivation_requests(AdminService.get_pending_reactivations())
                )
                if req_id == 0:
                    continue
                    
                req = next((r for r in reqs if r['request_id'] == req_id), None)
                if not req:
                    print_error("Request not found.")
                    continue
                    
                print("1. Approve")
                print("2. Reject")
                action_choice = get_input("Select action: ", cast_type=int)
                
                action_map = {1: "APPROVE", 2: "REJECT"}
                if action_choice not in action_map:
                    print_error("Invalid action.")
                    continue
                    
                remarks = get_input("Enter Remarks (optional): ", allow_empty=True)
                try:
                    AdminService.process_reactivation(user['user_id'], req_id, req['user_id'], action_map[action_choice], remarks)
                    print_success(f"Request {action_map[action_choice]}.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 4:
                c_id = get_input(
                    "Enter Customer User ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_users(AdminService.get_users_by_role(Role.CUSTOMER))
                )
                a_id = get_input(
                    "Enter Policy Agent ID to assign: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_users(AdminService.get_users_by_role(Role.POLICY_AGENT))
                )
                try:
                    AdminService.assign_policy_agent(c_id, a_id)
                    print_success("Agent assigned successfully.")
                except AppError as e:
                    print_error(str(e))

    @staticmethod
    def agent_management(user: dict):
        while True:
            display_header("STAFF & AGENT MANAGEMENT")
            print("1. Add Policy Agent / Claim Officer")
            print("2. View All Agents/Officers")
            print("3. Edit Policy Agent / Claim Officer")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                name = get_input("Full Name: ")
                email = get_input("Email: ")
                password = get_input("Password: ", is_password=True)
                phone = get_input("Phone (+91 XXXXXXXXXX): ")
                dob = get_input("Date of Birth (YYYY-MM-DD): ")
                print(f"Roles: {Role.POLICY_AGENT}, {Role.CLAIM_OFFICER}")
                role = get_input("Role: ").upper()
                try:
                    AdminService.add_staff(name, email, password, phone, dob, role)
                    print_success(f"Successfully added {name} as {role}.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 2:
                staff = AdminService.get_staff_members()
                Menus.print_users(staff)
            elif choice == 3:
                staff_id = get_input(
                    "Enter Agent/Officer User ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_users(AdminService.get_users_by_role(Role.POLICY_AGENT))
                )
                print("\n1. Update Phone Number")
                print("2. Toggle Active Status")
                print("0. Cancel")
                sub_choice = get_input("Select action: ", cast_type=int)
                if sub_choice == 0:
                    continue
                
                try:
                    if sub_choice == 1:
                        new_phone = get_input("Enter new phone: ")
                        AdminService.update_staff_phone(staff_id, new_phone)
                        print_success("Phone updated.")
                    elif sub_choice == 2:
                        AdminService.toggle_staff_status(staff_id)
                        print_success("Staff status toggled.")
                    else:
                        print_error("Invalid action.")
                except AppError as e:
                    print_error(str(e))

    @staticmethod
    def claim_management(user: dict):
        while True:
            display_header("ADMIN CLAIM MANAGEMENT")
            print("1. View Unassigned Claim Pool")
            print("2. Assign Claim to Officer")
            print("3. View All Claims")
            print("4. Search Claim by ID")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                pool = AdminService.get_unassigned_claims()
                Menus.print_my_claims(pool, admin_mode=True)
            elif choice == 2:
                claim_id = get_input(
                    "Enter Claim ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_claims(AdminService.get_unassigned_claims(), admin_mode=True)
                )
                officer_id = get_input(
                    "Enter Claim Officer ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_users(AdminService.get_users_by_role(Role.CLAIM_OFFICER))
                )
                try:
                    AdminService.assign_claim(user['user_id'], claim_id, officer_id)
                    print_success("Claim assigned successfully.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 3:
                claims = AdminService.get_all_claims()
                Menus.print_my_claims(claims, admin_mode=True)
            elif choice == 4:
                claim_id = get_input(
                    "Enter Claim ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_claims(AdminService.get_all_claims(), admin_mode=True)
                )
                claim = AdminService.get_claim_by_id(claim_id)
                if claim:
                    Menus.print_my_claims([claim], admin_mode=True)
                else:
                    print_error("Claim not found.")

    @staticmethod
    def policy_management(user: dict):
        while True:
            display_header("ADMIN POLICY MANAGEMENT")
            print("1. View All Customer Policies")
            print("2. Search Customer Policy by ID")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                policies = AdminService.get_all_customer_policies()
                Menus.print_my_policies(policies, admin_mode=True)
            elif choice == 2:
                cp_id = get_input(
                    "Enter Customer Policy ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_policies(AdminService.get_all_customer_policies(), admin_mode=True)
                )
                policy = AdminService.get_customer_policy_by_id(cp_id)
                if policy:
                    Menus.print_my_policies([policy], admin_mode=True)
                else:
                    print_error("Policy not found.")

    @staticmethod
    def reports(user: dict):
        while True:
            display_header("SYSTEM REPORTS")
            print("1. Active Policies Report")
            print("2. Approved Claims Report")
            print("3. Expired Policies Report")
            print("4. Rejected Claims Report")
            print("5. Agent Performance Report")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                display_header("REPORT: ACTIVE POLICIES")
                policies = AdminService.get_active_policies_report()
                print_info(f"Total Active Policies: {len(policies)}")
                for p in policies:
                    Menus.print_report_card(p, "ACTIVE POLICY")
            elif choice == 2:
                display_header("REPORT: APPROVED CLAIMS")
                claims = AdminService.get_approved_claims_report()
                print_info(f"Total Approved Claims: {len(claims)}")
                for c in claims:
                    Menus.print_report_card(c, "APPROVED CLAIM")
            elif choice == 3:
                display_header("REPORT: EXPIRED POLICIES")
                policies = AdminService.get_expired_policies_report()
                print_info(f"Total Expired Policies: {len(policies)}")
                for p in policies:
                    Menus.print_report_card(p, "EXPIRED POLICY")
            elif choice == 4:
                display_header("REPORT: REJECTED CLAIMS")
                claims = AdminService.get_rejected_claims_report()
                print_info(f"Total Rejected Claims: {len(claims)}")
                for c in claims:
                    Menus.print_report_card(c, "REJECTED CLAIM")
            elif choice == 5:
                display_header("REPORT: AGENT PERFORMANCE")
                agents = AdminService.get_agent_performance_report()
                print_info(f"Total Agents: {len(agents)}")
                for a in agents:
                    Menus.print_report_card(a, "AGENT PERFORMANCE")
            else:
                print_error("Invalid option.")
