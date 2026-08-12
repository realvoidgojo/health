from typing import Dict, Any
from app.repositories.user_repository import UserRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.claim_repository import ClaimRepository
from app.core.validators import validate_phone, validate_date, calculate_age
from app.core.exceptions import ValidationError, BusinessRuleError
from app.core.constants import PolicyStatus, ClaimStatus, ClaimAction

class CustomerService:
    @staticmethod
    def update_profile(user_id: int, field: str, value: str) -> None:
        if field == "phone" and not validate_phone(value):
            raise ValidationError("Invalid phone format.")
        if field == "date_of_birth" and not validate_date(value):
            raise ValidationError("Invalid date format.")
            
        UserRepository.update_field(user_id, field, value)
        
    @staticmethod
    def delete_account(user_id: int) -> None:
        UserRepository.soft_delete(user_id)
        
    @staticmethod
    def get_suggested_policies(dob: str) -> list:
        age = calculate_age(dob)
        if age >= 60:
            categories = ['Senior Citizen Plan']
        else:
            categories = ['Individual Plan', 'Family Floater Plan']
            
        return PolicyRepository.get_master_policies_by_category(categories)
        
    @staticmethod
    def purchase_policy(customer_id: int, policy_id: int, nominee_name: str, nominee_relation: str, assigned_agent_id: int) -> None:
        master = PolicyRepository.get_master_policy_by_id(policy_id)
        if not master:
            raise ValidationError("Policy does not exist or is inactive.")
            
        duplicate = PolicyRepository.check_duplicate_purchase(customer_id, policy_id)
        if duplicate:
            raise BusinessRuleError("You already have an active or pending purchase for this policy.")
            
        PolicyRepository.create_customer_policy(customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id)
        
    @staticmethod
    def update_nominee(customer_id: int, cp_id: int, new_nominee: str, new_relation: str) -> None:
        policy = PolicyRepository.get_customer_policy_by_id(cp_id, customer_id)
        if not policy:
            raise ValidationError("Policy not found.")
            
        if policy['status'] != PolicyStatus.ACTIVE:
            raise BusinessRuleError("Nominee can only be updated for active policies.")
            
        PolicyRepository.update_nominee(cp_id, customer_id, new_nominee, new_relation)
        
    @staticmethod
    def renew_policy(customer_id: int, cp_id: int) -> None:
        policy = PolicyRepository.get_customer_policy_by_id(cp_id, customer_id)
        if not policy:
            raise ValidationError("Policy not found.")
            
        if policy['status'] != PolicyStatus.EXPIRED:
            raise BusinessRuleError("Only expired policies can be renewed.")
            
        # Parse current expiry, add 1 year
        from datetime import datetime
        try:
            curr_expiry = datetime.strptime(policy['expiry_date'], "%Y-%m-%d")
            new_expiry = curr_expiry.replace(year=curr_expiry.year + 1).strftime("%Y-%m-%d")
        except Exception:
            new_expiry = "2099-12-31" # Fallback
            
        PolicyRepository.renew_policy(cp_id, new_expiry)
        
    @staticmethod
    def cancel_policy(customer_id: int, cp_id: int) -> None:
        policy = PolicyRepository.get_customer_policy_by_id(cp_id, customer_id)
        if not policy:
            raise ValidationError("Policy not found.")
            
        if policy['status'] != PolicyStatus.ACTIVE:
            raise BusinessRuleError("Only active policies can be cancelled.")
            
        PolicyRepository.cancel_policy(cp_id, customer_id)

    @staticmethod
    def file_claim(customer_id: int, cp_id: int, claim_amount: float, claim_reason: str) -> None:
        policy = PolicyRepository.get_customer_policy_with_sum_insured(cp_id, customer_id)
        if not policy:
            raise ValidationError("Policy not found.")
            
        if policy['status'] != PolicyStatus.ACTIVE:
            raise BusinessRuleError("Claims can only be filed against active policies.")
            
        if claim_amount > policy['sum_insured']:
            raise BusinessRuleError(f"Claim amount cannot exceed sum insured (₹{policy['sum_insured']}).")
            
        ClaimRepository.create_claim(cp_id, customer_id, claim_amount, claim_reason)

    @staticmethod
    def update_claim(customer_id: int, claim_id: int, additional_details: str) -> None:
        claim = ClaimRepository.get_claim_status_for_customer(claim_id, customer_id)
        if not claim:
            raise ValidationError("Claim not found.")
            
        if claim['status'] != ClaimStatus.NEEDS_UPDATE:
            raise BusinessRuleError("Claim does not require updates.")
            
        ClaimRepository.update_claim_details(claim_id, additional_details, ClaimStatus.UNDER_REVIEW)
        # Adding to claim history logic isn't tied to an officer here, usually history is kept for officers.
        # But in the old code, it logged CUSTOMER_UPDATED using customer's ID as officer_id.
        ClaimRepository.add_claim_history(claim_id, customer_id, ClaimAction.CUSTOMER_UPDATED, "Customer updated claim details")
