from typing import TypedDict

class MasterPolicy(TypedDict):
    policy_id: int
    policy_name: str
    category: str
    sum_insured: float
    premium: float
    coverage_details: str
    is_active: int
