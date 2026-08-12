import sys
import getpass
from app.controllers.auth_controller import AuthController
from app.controllers.customer_controller import CustomerController
from app.controllers.agent_controller import AgentController
from app.controllers.officer_controller import OfficerController
from app.controllers.admin_controller import AdminController
from app.views.console.ui import display_header, get_input, print_info
from app.core.constants import Role

current_user = None

def register_user():
    AuthController.register()

def login_user():
    global current_user
    user = AuthController.login()
    if user:
        current_user = dict(user)
        return True
    return False

def request_reactivation():
    # Only for backwards compat if directly called in tests
    email = get_input("Enter Email: ")
    password = get_input("Enter Password: ", is_password=True)
    AuthController.request_reactivation_flow(email, password)

# Deprecated stubs to keep old tests green if they explicitly import main.X
def customer_profile_menu():
    global current_user
    if CustomerController.profile_menu(current_user):
        current_user = None
def customer_policy_menu():
    CustomerController.policy_menu(current_user)
def customer_claim_menu():
    CustomerController.claim_menu(current_user)
def customer_dashboard():
    global current_user
    CustomerController.dashboard(current_user)
    current_user = None
def agent_dashboard():
    global current_user
    AgentController.dashboard(current_user)
    current_user = None
def officer_dashboard():
    global current_user
    OfficerController.dashboard(current_user)
    current_user = None
def admin_user_management():
    AdminController.user_management(current_user)
def admin_agent_management():
    AdminController.agent_management(current_user)
def admin_claim_management():
    AdminController.claim_management(current_user)
def admin_policy_management():
    AdminController.policy_management(current_user)
def admin_reports():
    AdminController.reports(current_user)
def admin_dashboard():
    global current_user
    AdminController.dashboard(current_user)
    current_user = None

def main():
    global current_user
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
            login_user()
            if current_user:
                role = current_user['role']
                if role == Role.CUSTOMER:
                    customer_dashboard()
                elif role == Role.POLICY_AGENT:
                    agent_dashboard()
                elif role == Role.CLAIM_OFFICER:
                    officer_dashboard()
                elif role == Role.ADMIN:
                    admin_dashboard()
        elif choice == 3:
            request_reactivation()
        elif choice == 0:
            print_info("Exiting system. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
