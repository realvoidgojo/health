from typing import TypedDict, Optional

class ReactivationRequest(TypedDict):
    request_id: int
    user_id: int
    status: str
    admin_remarks: Optional[str]
    created_at: str
    
    # Extended fields from JOINs
    email: Optional[str]
