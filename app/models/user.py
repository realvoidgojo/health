from typing import TypedDict, Optional

class User(TypedDict):
    user_id: int
    full_name: str
    email: str
    password: str
    phone: str
    date_of_birth: str
    role: str
    assigned_agent_id: Optional[int]
    is_active: int
    is_deleted: int
    created_at: str
