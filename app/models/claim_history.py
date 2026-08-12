from typing import TypedDict, Optional

class ClaimHistory(TypedDict):
    history_id: int
    claim_id: int
    officer_id: int
    action_taken: str
    remarks: Optional[str]
    created_at: str
