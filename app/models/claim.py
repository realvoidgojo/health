from typing import TypedDict, Optional

class Claim(TypedDict):
    claim_id: int
    customer_policy_id: int
    customer_id: int
    claim_amount: float
    claim_reason: str
    additional_details: Optional[str]
    status: str
    claim_officer_id: Optional[int]
    created_at: str
    updated_at: str
    
    # Extended fields from JOINs
    cust_name: Optional[str]
    policy_id: Optional[int]
    policy_name: Optional[str]
    officer_name: Optional[str]
    cust_email: Optional[str]
