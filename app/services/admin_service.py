from typing import Dict, Any, List
from app.repositories.user_repository import UserRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.reactivation_repository import ReactivationRepository
from app.repositories.report_repository import ReportRepository
from app.core.security import hash_password
from app.core.validators import validate_email, validate_phone, validate_date
from app.core.exceptions import ValidationError, BusinessRuleError
from app.core.constants import Role, ReactivationStatus, ClaimStatus, ClaimAction

class AdminService:
    # --- User Management ---
    @staticmethod
    def get_all_users():
        return UserRepository.get_all_users()
        
    @staticmethod
    def assign_policy_agent(customer_id: int, agent_id: int):
        customer = UserRepository.get_by_id(customer_id)
        if not customer or customer['role'] != Role.CUSTOMER:
            raise ValidationError("Invalid Customer ID.")
            
        agent = UserRepository.get_by_id(agent_id)
        if not agent or agent['role'] != Role.POLICY_AGENT or not agent['is_active'] or agent['is_deleted']:
            raise ValidationError("Invalid or inactive Policy Agent ID.")
            
        UserRepository.update_field(customer_id, 'assigned_agent_id', agent_id)
        PolicyRepository.update_agent_for_pending_policies(customer_id, agent_id)
    @staticmethod
    def get_users_by_role(role: str):
        return UserRepository.get_users_by_role(role)
        
    @staticmethod
    def search_user_by_email(email: str):
        return UserRepository.get_by_email(email)
        
    @staticmethod
    def get_pending_reactivations():
        return ReactivationRepository.get_all_pending_requests()
        
    @staticmethod
    def process_reactivation(admin_id: int, request_id: int, user_id: int, action: str, remarks: str = None):
        if action == "APPROVE":
            ReactivationRepository.update_request_status(request_id, ReactivationStatus.APPROVED, remarks)
            UserRepository.reactivate(user_id)
        elif action == "REJECT":
            ReactivationRepository.update_request_status(request_id, ReactivationStatus.REJECTED, remarks)
        else:
            raise ValidationError("Invalid action.")

    # --- Agent/Staff Management ---
    @staticmethod
    def add_staff(full_name: str, email: str, password: str, phone: str, date_of_birth: str, role: str):
        if role not in (Role.POLICY_AGENT, Role.CLAIM_OFFICER):
            raise ValidationError("Invalid staff role.")
            
        if not validate_email(email):
            raise ValidationError("Invalid email format.")
            
        if not validate_phone(phone):
            raise ValidationError("Invalid phone format.")
            
        if not validate_date(date_of_birth):
            raise ValidationError("Invalid date format.")
            
        if UserRepository.get_by_email(email):
            raise ValidationError("An account with this email already exists.")
            
        hashed = hash_password(password)
        UserRepository.create_staff(full_name, email, hashed, phone, date_of_birth, role)
        
    @staticmethod
    def get_staff_members():
        return UserRepository.get_staff_members()
        
    @staticmethod
    def toggle_staff_status(user_id: int):
        user = UserRepository.get_by_id(user_id)
        if not user or user['role'] not in (Role.POLICY_AGENT, Role.CLAIM_OFFICER):
            raise ValidationError("Staff member not found.")
            
        new_status = 0 if user['is_active'] else 1
        UserRepository.update_field(user_id, 'is_active', new_status)
        
    @staticmethod
    def update_staff_phone(user_id: int, phone: str):
        user = UserRepository.get_by_id(user_id)
        if not user or user['role'] not in (Role.POLICY_AGENT, Role.CLAIM_OFFICER):
            raise ValidationError("Staff member not found.")
            
        if not validate_phone(phone):
            raise ValidationError("Invalid phone format.")
            
        UserRepository.update_field(user_id, 'phone', phone)

    # --- Claim Management ---
    @staticmethod
    def get_unassigned_claims():
        return ClaimRepository.get_unassigned_claims()
        
    @staticmethod
    def assign_claim(admin_id: int, claim_id: int, officer_id: int):
        officer = UserRepository.get_by_id(officer_id)
        if not officer or officer['role'] != Role.CLAIM_OFFICER or not officer['is_active']:
            raise ValidationError("Valid and active Claim Officer ID is required.")
            
        claim = ClaimRepository.get_claim_by_id(claim_id)
        if not claim or claim['status'] != ClaimStatus.PENDING_ASSIGNMENT:
            raise BusinessRuleError("Claim is not pending assignment.")
            
        ClaimRepository.assign_claim(claim_id, officer_id)
        ClaimRepository.add_claim_history(claim_id, admin_id, ClaimAction.ASSIGNED, f"Assigned to officer {officer_id}")
        
    @staticmethod
    def get_all_claims():
        return ClaimRepository.get_all_claims()
        
    @staticmethod
    def get_claim_by_id(claim_id: int):
        return ClaimRepository.get_claim_by_id(claim_id)
        
    # --- Policy Management ---
    @staticmethod
    def get_all_customer_policies():
        return PolicyRepository.get_all_customer_policies()
        
    @staticmethod
    def get_customer_policy_by_id(cp_id: int):
        # Admin can view anyone's policy, so we reuse the basic fetch but need a custom repo method 
        # or we can just fetch all and filter for now to avoid writing too many repo methods
        all_policies = PolicyRepository.get_all_customer_policies()
        return next((p for p in all_policies if p['customer_policy_id'] == cp_id), None)
        
    @staticmethod
    def get_system_reports():
        active_policies = ReportRepository.get_active_policies_count()
        expired_policies = ReportRepository.get_expired_policies_count()
        approved_claims_count, approved_claims_amount = ReportRepository.get_approved_claims_stats()
        rejected_claims_count, rejected_claims_amount = ReportRepository.get_rejected_claims_stats()
        
        return {
            "active_policies": active_policies,
            "expired_policies": expired_policies,
            "approved_claims_count": approved_claims_count,
            "approved_claims_amount": approved_claims_amount,
            "rejected_claims_count": rejected_claims_count,
            "rejected_claims_amount": rejected_claims_amount
        }

    @staticmethod
    def get_active_policies_report():
        return ReportRepository.get_active_policies_report()

    @staticmethod
    def get_expired_policies_report():
        return ReportRepository.get_expired_policies_report()

    @staticmethod
    def get_approved_claims_report():
        return ReportRepository.get_approved_claims_report()

    @staticmethod
    def get_rejected_claims_report():
        return ReportRepository.get_rejected_claims_report()

    @staticmethod
    def get_agent_performance_report():
        return ReportRepository.get_agent_performance_report()
