from app.services.agent_service import AgentService
from app.repositories.policy_repository import PolicyRepository
from app.views.console.ui import display_header, get_input, print_success, print_error, print_info
from app.views.console.menus import Menus
from app.core.exceptions import AppError

class AgentController:
    @staticmethod
    def dashboard(user: dict):
        while True:
            display_header(f"AGENT DASHBOARD - {user['full_name']}")
            print("1. View Assigned Customers")
            print("2. View Assigned Customer Policies")
            print("3. Process Policy Requests (Approve/Reject)")
            print("0. Logout")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                print_success("Logging out...")
                break
                
            if choice == 1:
                customers = AgentService.get_assigned_customers(user['user_id'])
                Menus.print_users(customers)
            elif choice == 2:
                policies = AgentService.get_assigned_customer_policies(user['user_id'])
                Menus.print_my_policies(policies)
            elif choice == 3:
                AgentController.review_pending_policies(user)
            else:
                print_error("Invalid option.")
                
    @staticmethod
    def review_pending_policies(user: dict):
        while True:
            display_header("PENDING POLICY REQUESTS")
            pending = AgentService.get_pending_policies(user['user_id'])
            
            if not pending:
                print_info("No pending policy requests assigned to you.")
                break
                
            # Print using the admin mode of my policies view to show customer names
            Menus.print_my_policies(pending, admin_mode=True)
            
            print("\n1. Approve Policy")
            print("2. Reject Policy")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                cp_id = get_input(
                    "Enter Customer Policy ID to approve: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_pending_policies(AgentService.get_pending_policies())
                )
                remarks = get_input("Enter Remarks (optional): ", allow_empty=True)
                try:
                    AgentService.approve_policy(user['user_id'], cp_id, remarks)
                    print_success("Policy approved and activated.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 2:
                cp_id = get_input(
                    "Enter Customer Policy ID to reject: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_pending_policies(AgentService.get_pending_policies())
                )
                remarks = get_input("Enter Rejection Reason: ")
                suggest = get_input("Would you like to suggest a different policy? (Y/N): ")
                
                suggested_id = None
                if suggest.lower() == 'y':
                    suggested_id = get_input(
                        "Enter Suggested Master Policy ID: ", 
                        cast_type=int,
                        view_callback=lambda: Menus.print_available_policies(PolicyRepository.get_active_master_policies())
                    )
                    
                try:
                    AgentService.reject_policy(user['user_id'], cp_id, remarks, suggested_id)
                    print_success("Policy rejected.")
                except AppError as e:
                    print_error(str(e))
