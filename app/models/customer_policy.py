from typing import TypedDict, Optional

class CustomerPolicy(TypedDict):
    customer_policy_id: int
    customer_id: int
    policy_id: int
    nominee_name: str
    nominee_relation: str
    status: str
    start_date: Optional[str]
    expiry_date: Optional[str]
    assigned_agent_id: Optional[int]
    agent_remarks: Optional[str]
    suggested_policy_id: Optional[int]
    created_at: str
    
    # Extended fields from JOINs
    policy_name: Optional[str]
    cust_name: Optional[str]
