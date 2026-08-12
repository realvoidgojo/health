from typing import Optional
from app.repositories.policy_repository import PolicyRepository
from app.repositories.user_repository import UserRepository
from app.core.constants import PolicyStatus
from app.core.exceptions import ValidationError, BusinessRuleError

class AgentService:
    @staticmethod
    def get_assigned_customers(agent_id: int):
        return UserRepository.get_customers_by_agent(agent_id)
        
    @staticmethod
    def get_assigned_customer_policies(agent_id: int):
        return PolicyRepository.get_assigned_policies_by_agent(agent_id)

    @staticmethod
    def get_pending_policies(agent_id: int):
        return PolicyRepository.get_pending_policies_by_agent(agent_id)
        
    @staticmethod
    def approve_policy(agent_id: int, cp_id: int, remarks: str = None) -> None:
        from datetime import datetime
        
        # Verify the policy exists and belongs to this agent
        pending = PolicyRepository.get_pending_policies_by_agent(agent_id)
        policy = next((p for p in pending if p['customer_policy_id'] == cp_id), None)
        
        if not policy:
            raise ValidationError("Policy not found or not assigned to you.")
            
        start_date = datetime.now()
        expiry_date = start_date.replace(year=start_date.year + 1)
        
        PolicyRepository.update_policy_status_by_agent(
            cp_id, 
            status=PolicyStatus.ACTIVE,
            start_date=start_date.strftime("%Y-%m-%d"),
            expiry_date=expiry_date.strftime("%Y-%m-%d"),
            remarks=remarks
        )

    @staticmethod
    def reject_policy(agent_id: int, cp_id: int, remarks: str, suggested_policy_id: Optional[int] = None) -> None:
        # Verify the policy exists and belongs to this agent
        pending = PolicyRepository.get_pending_policies_by_agent(agent_id)
        policy = next((p for p in pending if p['customer_policy_id'] == cp_id), None)
        
        if not policy:
            raise ValidationError("Policy not found or not assigned to you.")
            
        if suggested_policy_id:
            master = PolicyRepository.get_master_policy_by_id(suggested_policy_id)
            if not master:
                raise ValidationError("Suggested policy ID does not exist or is inactive.")
                
        PolicyRepository.update_policy_status_by_agent(
            cp_id,
            status=PolicyStatus.REJECTED,
            remarks=remarks,
            suggested_policy_id=suggested_policy_id
        )
