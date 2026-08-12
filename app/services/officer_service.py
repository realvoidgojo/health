from app.repositories.claim_repository import ClaimRepository
from app.core.exceptions import ValidationError, BusinessRuleError
from app.core.constants import ClaimStatus, ClaimAction

class OfficerService:
    @staticmethod
    def get_assigned_claims(officer_id: int):
        return ClaimRepository.get_assigned_claims_by_officer(officer_id)
        
    @staticmethod
    def process_claim(officer_id: int, claim_id: int, action: str, remarks: str = None) -> None:
        assigned = ClaimRepository.get_assigned_claims_by_officer(officer_id)
        claim = next((c for c in assigned if c['claim_id'] == claim_id), None)
        
        if not claim:
            raise ValidationError("Claim not found or not assigned to you.")
            
        if action == "APPROVE":
            new_status = ClaimStatus.APPROVED
            history_action = ClaimAction.APPROVED
        elif action == "REJECT":
            new_status = ClaimStatus.REJECTED
            history_action = ClaimAction.REJECTED
            if not remarks:
                raise ValidationError("Remarks are mandatory when rejecting.")
        elif action == "REQUEST_UPDATE":
            new_status = ClaimStatus.NEEDS_UPDATE
            history_action = ClaimAction.REQUESTED_UPDATE
            if not remarks:
                raise ValidationError("Remarks are mandatory when requesting an update.")
        else:
            raise ValidationError("Invalid action.")
            
        ClaimRepository.update_claim_status(claim_id, new_status)
        ClaimRepository.add_claim_history(claim_id, officer_id, history_action, remarks)
        
    @staticmethod
    def get_claim_history(claim_id: int):
        return ClaimRepository.get_claim_history(claim_id)
