from app.services.customer_service import CustomerService
from app.repositories.policy_repository import PolicyRepository
from app.repositories.claim_repository import ClaimRepository
from app.views.console.ui import display_header, get_input, print_success, print_error
from app.views.console.menus import Menus
from app.core.exceptions import AppError
from app.core.validators import calculate_age
import sys

class CustomerController:
    @staticmethod
    def dashboard(user: dict):
        while True:
            display_header(f"CUSTOMER DASHBOARD - {user['full_name']}")
            print("1. Profile Management")
            print("2. Policy Management")
            print("3. Claim Management")
            print("0. Logout")
            
            choice = get_input("Select an option: ", cast_type=int)
            
            if choice == 1:
                if CustomerController.profile_menu(user):
                    # User deleted themselves
                    return
            elif choice == 2:
                CustomerController.policy_menu(user)
            elif choice == 3:
                CustomerController.claim_menu(user)
            elif choice == 0:
                print_success("Logging out...")
                break
            else:
                print_error("Invalid option.")

    @staticmethod
    def profile_menu(user: dict) -> bool:
        while True:
            display_header("CUSTOMER PROFILE")
            print("1. View Profile")
            print("2. Edit Profile")
            print("3. Delete Account")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                return False
                
            if choice == 1:
                from app.views.console.ui import print_card
                print_card(f"PROFILE: {user['full_name']}", [
                    ("User ID", user['user_id']),
                    ("Email", user['email']),
                    ("Phone", user['phone']),
                    ("Date of Birth", user['date_of_birth']),
                    ("Role", user['role'])
                ])
            elif choice == 2:
                print("\n1. Update Name")
                print("2. Update Phone")
                print("3. Update Date of Birth")
                print("0. Cancel")
                
                sub_choice = get_input("Select field to update: ", cast_type=int)
                if sub_choice == 0:
                    continue
                    
                if sub_choice in (1, 2, 3):
                    field_map = {1: 'full_name', 2: 'phone', 3: 'date_of_birth'}
                    field = field_map[sub_choice]
                    new_val = get_input(f"New {field.replace('_', ' ').title()}: ")
                    
                    try:
                        CustomerService.update_profile(user['user_id'], field, new_val)
                        user[field] = new_val  # update local session
                        print_success("Profile updated.")
                    except AppError as e:
                        print_error(str(e))
                else:
                    print_error("Invalid option.")
                    
            elif choice == 3:
                confirm = get_input("Are you sure you want to delete your account? (Y/N): ")
                if confirm.lower() == 'y':
                    try:
                        CustomerService.delete_account(user['user_id'])
                        print_success("Account deleted successfully.")
                        return True
                    except AppError as e:
                        print_error(str(e))
            else:
                print_error("Invalid option.")

    @staticmethod
    def policy_menu(user: dict):
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
            if choice == 0:
                break
                
            if choice == 1:
                policies = PolicyRepository.get_active_master_policies()
                Menus.print_available_policies(policies)
            elif choice == 2:
                policy_id = get_input(
                    "Enter Policy ID to purchase: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_available_policies(PolicyRepository.get_active_master_policies())
                )
                nominee = get_input("Enter Nominee Name: ")
                relation = get_input("Enter Nominee Relation: ")
                try:
                    CustomerService.purchase_policy(user['user_id'], policy_id, nominee, relation, user['assigned_agent_id'])
                    print_success("Policy purchase requested successfully! Pending agent approval.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 3:
                policies = PolicyRepository.get_customer_policies(user['user_id'])
                Menus.print_my_policies(policies)
            elif choice == 4:
                age = calculate_age(user['date_of_birth'])
                print(f"Based on your age ({age} years), we recommend the following plans:\n")
                policies = CustomerService.get_suggested_policies(user['date_of_birth'])
                Menus.print_available_policies(policies)
            elif choice == 5:
                cp_id = get_input(
                    "Enter Customer Policy ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_policies(PolicyRepository.get_customer_policies(user['user_id']))
                )
                new_nominee = get_input("Enter new Nominee Name: ")
                new_relation = get_input("Enter new Nominee Relation: ")
                try:
                    CustomerService.update_nominee(user['user_id'], cp_id, new_nominee, new_relation)
                    print_success("Nominee updated.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 6:
                cp_id = get_input(
                    "Enter Customer Policy ID to renew: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_policies(PolicyRepository.get_customer_policies(user['user_id']))
                )
                try:
                    CustomerService.renew_policy(user['user_id'], cp_id)
                    print_success("Policy renewed successfully for 1 year.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 7:
                cp_id = get_input(
                    "Enter Customer Policy ID to cancel: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_policies(PolicyRepository.get_customer_policies(user['user_id']))
                )
                confirm = get_input("Are you sure you want to cancel this policy? (Y/N): ")
                if confirm.lower() == 'y':
                    try:
                        CustomerService.cancel_policy(user['user_id'], cp_id)
                        print_success("Policy cancelled successfully.")
                    except AppError as e:
                        print_error(str(e))

    @staticmethod
    def claim_menu(user: dict):
        while True:
            display_header("CLAIM MANAGEMENT")
            print("1. File Claim")
            print("2. View My Claims")
            print("3. Update Claim Details")
            print("0. Back")
            
            choice = get_input("Select an option: ", cast_type=int)
            if choice == 0:
                break
                
            if choice == 1:
                cp_id = get_input(
                    "Enter Customer Policy ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_policies(PolicyRepository.get_customer_policies(user['user_id']))
                )
                amt = get_input("Enter Claim Amount: ₹", cast_type=float)
                reason = get_input("Enter Claim Reason: ")
                try:
                    CustomerService.file_claim(user['user_id'], cp_id, amt, reason)
                    print_success("Claim filed successfully and is pending assignment.")
                except AppError as e:
                    print_error(str(e))
            elif choice == 2:
                claims = ClaimRepository.get_claims_by_customer(user['user_id'])
                Menus.print_my_claims(claims)
            elif choice == 3:
                claim_id = get_input(
                    "Enter Claim ID: ", 
                    cast_type=int,
                    view_callback=lambda: Menus.print_my_claims(ClaimRepository.get_claims_by_customer(user['user_id']))
                )
                details = get_input("Enter updated details/documents text: ")
                try:
                    CustomerService.update_claim(user['user_id'], claim_id, details)
                    print_success("Claim updated successfully.")
                except AppError as e:
                    print_error(str(e))
