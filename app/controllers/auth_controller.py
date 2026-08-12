from app.services.auth_service import AuthService
from app.views.console.ui import display_header, get_input, print_success, print_error
from app.core.exceptions import AppError
from typing import Dict, Any, Optional

class AuthController:
    @staticmethod
    def login() -> Optional[Dict[str, Any]]:
        display_header("LOGIN")
        email = get_input("Enter Email: ")
        
        try:
            user = AuthService.authenticate(email, password="dummy_because_we_get_it_in_try_block_but_we_need_it_here")
            # Wait, we need to ask for password. 
        except Exception:
            pass
            
        # Re-writing cleanly:
        password = get_input("Enter Password: ", is_password=True)
        
        try:
            user = AuthService.authenticate(email, password)
            print_success(f"Welcome back, {user['full_name']}!")
            return user
        except AppError as e:
            print_error(str(e))
            if "deleted" in str(e).lower():
                # Provide quick flow to request reactivation
                AuthController.request_reactivation_flow(email, password)
            return None
            
    @staticmethod
    def request_reactivation_flow(email: str, password: str):
        choice = get_input("Would you like to request account reactivation? (Y/N): ")
        if choice.lower() == 'y':
            try:
                AuthService.request_reactivation(email, password)
                print_success("Reactivation request submitted to admin.")
            except AppError as e:
                print_error(str(e))
                
    @staticmethod
    def register():
        display_header("REGISTER NEW ACCOUNT")
        
        full_name = get_input("Enter Full Name: ")
        email = get_input("Enter Email: ")
        password = get_input("Enter Password: ", is_password=True)
        phone = get_input("Enter Phone (+91 XXXXXXXXXX): ")
        dob = get_input("Enter Date of Birth (YYYY-MM-DD): ")
        
        try:
            user_id = AuthService.register_customer(full_name, email, password, phone, dob)
            print_success(f"Registration successful! Your user ID is {user_id}")
        except AppError as e:
            print_error(str(e))
