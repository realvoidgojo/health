from typing import List, Optional
from app.core.db.base_repository import execute_query, fetch_one, fetch_all
from app.models.master_policy import MasterPolicy
from app.models.customer_policy import CustomerPolicy
from app.core.constants import PolicyStatus

class PolicyRepository:
    @staticmethod
    def get_active_master_policies() -> List[MasterPolicy]:
        return fetch_all("SELECT * FROM master_policies WHERE is_active = 1")
        
    @staticmethod
    def get_master_policies_by_category(categories: List[str]) -> List[MasterPolicy]:
        placeholders = ",".join(["?"] * len(categories))
        sql = f"SELECT * FROM master_policies WHERE category IN ({placeholders}) AND is_active = 1"
        return fetch_all(sql, tuple(categories))
        
    @staticmethod
    def get_master_policy_by_id(policy_id: int) -> Optional[MasterPolicy]:
        return fetch_one("SELECT * FROM master_policies WHERE policy_id = ? AND is_active = 1", (policy_id,))
        
    @staticmethod
    def get_customer_policies(customer_id: int) -> List[CustomerPolicy]:
        sql = """
            SELECT cp.*, mp.policy_name 
            FROM customer_policies cp 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE cp.customer_id = ?
        """
        return fetch_all(sql, (customer_id,))
        
    @staticmethod
    def get_customer_policy_by_id(cp_id: int, customer_id: int) -> Optional[CustomerPolicy]:
        return fetch_one("SELECT * FROM customer_policies WHERE customer_policy_id = ? AND customer_id = ?", (cp_id, customer_id))
        
    @staticmethod
    def get_customer_policy_with_sum_insured(cp_id: int, customer_id: int):
        sql = """
            SELECT cp.status, mp.sum_insured 
            FROM customer_policies cp 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE cp.customer_policy_id = ? AND cp.customer_id = ?
        """
        return fetch_one(sql, (cp_id, customer_id))
        
    @staticmethod
    def check_duplicate_purchase(customer_id: int, policy_id: int) -> Optional[CustomerPolicy]:
        sql = """
            SELECT * FROM customer_policies 
            WHERE customer_id = ? AND policy_id = ? 
            AND status IN (?, ?)
        """
        return fetch_one(sql, (customer_id, policy_id, PolicyStatus.PENDING_APPROVAL, PolicyStatus.ACTIVE))
        
    @staticmethod
    def create_customer_policy(customer_id: int, policy_id: int, nominee_name: str, nominee_relation: str, assigned_agent_id: int) -> int:
        sql = """
            INSERT INTO customer_policies (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id) 
            VALUES (?, ?, ?, ?, ?)
        """
        return execute_query(sql, (customer_id, policy_id, nominee_name, nominee_relation, assigned_agent_id))
        
    @staticmethod
    def update_nominee(cp_id: int, customer_id: int, nominee_name: str, nominee_relation: str) -> int:
        sql = """
            UPDATE customer_policies 
            SET nominee_name = ?, nominee_relation = ? 
            WHERE customer_policy_id = ? AND customer_id = ? AND status = ?
        """
        return execute_query(sql, (nominee_name, nominee_relation, cp_id, customer_id, PolicyStatus.ACTIVE))
        
    @staticmethod
    def renew_policy(cp_id: int, new_expiry: str) -> int:
        sql = "UPDATE customer_policies SET status = ?, expiry_date = ? WHERE customer_policy_id = ?"
        return execute_query(sql, (PolicyStatus.ACTIVE, new_expiry, cp_id))
        
    @staticmethod
    def cancel_policy(cp_id: int, customer_id: int) -> int:
        sql = "UPDATE customer_policies SET status = ? WHERE customer_policy_id = ? AND customer_id = ? AND status IN (?, ?)"
        return execute_query(sql, (PolicyStatus.CANCELLED, cp_id, customer_id, PolicyStatus.ACTIVE, PolicyStatus.PENDING_APPROVAL))
        
    @staticmethod
    def get_pending_policies_by_agent(agent_id: int) -> List[CustomerPolicy]:
        sql = """
            SELECT cp.*, u.full_name as cust_name, mp.policy_name 
            FROM customer_policies cp 
            JOIN users u ON cp.customer_id = u.user_id 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE cp.assigned_agent_id = ? AND cp.status = ?
        """
        return fetch_all(sql, (agent_id, PolicyStatus.PENDING_APPROVAL))
        
    @staticmethod
    def get_assigned_policies_by_agent(agent_id: int) -> List[CustomerPolicy]:
        sql = """
            SELECT cp.*, u.full_name as cust_name, mp.policy_name 
            FROM customer_policies cp 
            JOIN users u ON cp.customer_id = u.user_id 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE cp.assigned_agent_id = ?
        """
        return fetch_all(sql, (agent_id,))
        
    @staticmethod
    def update_policy_status_by_agent(cp_id: int, status: str, start_date: str = None, expiry_date: str = None, remarks: str = None, suggested_policy_id: int = None) -> int:
        sql = """
            UPDATE customer_policies 
            SET status = ?, start_date = ?, expiry_date = ?, agent_remarks = ?, suggested_policy_id = ? 
            WHERE customer_policy_id = ?
        """
        return execute_query(sql, (status, start_date, expiry_date, remarks, suggested_policy_id, cp_id))
        
    @staticmethod
    def get_all_customer_policies() -> List[CustomerPolicy]:
        sql = """
            SELECT cp.*, u.full_name as cust_name, mp.policy_name 
            FROM customer_policies cp 
            JOIN users u ON cp.customer_id = u.user_id 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
        """
        return fetch_all(sql)

    @staticmethod
    def update_agent_for_all_policies(customer_id: int, agent_id: int) -> int:
        sql = "UPDATE customer_policies SET assigned_agent_id = ? WHERE customer_id = ? AND status IN (?, ?)"
        return execute_query(sql, (agent_id, customer_id, PolicyStatus.PENDING_APPROVAL, PolicyStatus.ACTIVE))
