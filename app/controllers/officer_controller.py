from app.services.officer_service import OfficerService
from app.views.console.ui import display_header, get_input, print_success, print_error, print_info
from app.views.console.menus import Menus
from app.core.exceptions import AppError

class OfficerController:
    @staticmethod
    def dashboard(user: dict):
        while True:
            display_header(f"OFFICER DASHBOARD - {user['full_name']}")
            print("1. View Assigned Claims Queue")
            print("2. Review Claim")
            print("3. View Claim History Log")
            print("0. Logout")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                print_success("Logging out...")
                break
                
            if choice == 1:
                assigned = OfficerService.get_assigned_claims(user['user_id'])
                if not assigned:
                    print_info("No claims assigned to you require action.")
                else:
                    Menus.print_my_claims(assigned, admin_mode=True)
            elif choice == 2:
                claim_id = get_input(
                    "Enter Claim ID to process: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_claims(OfficerService.get_assigned_claims(user['user_id']), admin_mode=True)
                )
                print("1. Approve")
                print("2. Reject")
                print("3. Request More Info (Needs Update)")
                
                action_choice = get_input("Select action: ", cast_type=int)
                action_map = {1: "APPROVE", 2: "REJECT", 3: "REQUEST_UPDATE"}
                
                if action_choice not in action_map:
                    print_error("Invalid action.")
                    continue
                    
                remarks = get_input("Enter Remarks (mandatory for Reject/Request Update): ", allow_empty=(action_choice == 1))
                try:
                    OfficerService.process_claim(user['user_id'], claim_id, action_map[action_choice], remarks)
                    print_success(f"Claim successfully marked as {action_map[action_choice]}.")
                except AppError as e:
                    print_error(str(e))
                    
            elif choice == 3:
                claim_id = get_input(
                    "Enter Claim ID to view history: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_claims(OfficerService.get_assigned_claims(user['user_id']), admin_mode=True)
                )
                history = OfficerService.get_claim_history(claim_id)
                Menus.print_claim_history(history)
            else:
                print_error("Invalid option.")
