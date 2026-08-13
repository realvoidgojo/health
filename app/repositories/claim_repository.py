from typing import List, Optional
from app.core.db.base_repository import execute_query, fetch_one, fetch_all
from app.models.claim import Claim
from app.models.claim_history import ClaimHistory
from app.core.constants import ClaimStatus

class ClaimRepository:
    @staticmethod
    def get_claims_by_customer(customer_id: int) -> List[Claim]:
        return fetch_all("SELECT * FROM claims WHERE customer_id = ?", (customer_id,))
        
    @staticmethod
    def get_claim_status_for_customer(claim_id: int, customer_id: int) -> Optional[Claim]:
        return fetch_one("SELECT status FROM claims WHERE claim_id = ? AND customer_id = ?", (claim_id, customer_id))
        
    @staticmethod
    def get_cumulative_claim_amount(customer_policy_id: int) -> float:
        sql = "SELECT SUM(claim_amount) as total FROM claims WHERE customer_policy_id = ? AND status != ?"
        res = fetch_one(sql, (customer_policy_id, ClaimStatus.REJECTED))
        return res['total'] if res and res['total'] else 0.0
        
    @staticmethod
    def create_claim(customer_policy_id: int, customer_id: int, amount: float, reason: str) -> int:
        sql = """
            INSERT INTO claims (customer_policy_id, customer_id, claim_amount, claim_reason) 
            VALUES (?, ?, ?, ?)
        """
        return execute_query(sql, (customer_policy_id, customer_id, amount, reason))
        
    @staticmethod
    def update_claim_details(claim_id: int, details: str, new_status: str) -> int:
        sql = "UPDATE claims SET additional_details = ?, status = ? WHERE claim_id = ?"
        return execute_query(sql, (details, new_status, claim_id))
        
    @staticmethod
    def get_unassigned_claims() -> List[Claim]:
        sql = """
            SELECT c.*, u.full_name as cust_name, cp.policy_id 
            FROM claims c 
            JOIN users u ON c.customer_id = u.user_id 
            JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id 
            WHERE c.status = ?
        """
        return fetch_all(sql, (ClaimStatus.PENDING_ASSIGNMENT,))
        
    @staticmethod
    def assign_claim(claim_id: int, officer_id: int) -> int:
        sql = "UPDATE claims SET claim_officer_id = ?, status = ? WHERE claim_id = ?"
        return execute_query(sql, (officer_id, ClaimStatus.UNDER_REVIEW, claim_id))
        
    @staticmethod
    def get_assigned_claims_by_officer(officer_id: int) -> List[Claim]:
        sql = """
            SELECT c.*, u.full_name as cust_name, u.email as cust_email, mp.policy_name, cp.policy_id 
            FROM claims c 
            JOIN users u ON c.customer_id = u.user_id 
            JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE c.claim_officer_id = ? AND c.status IN (?, ?)
        """
        return fetch_all(sql, (officer_id, ClaimStatus.UNDER_REVIEW, ClaimStatus.NEEDS_UPDATE))
        
    @staticmethod
    def update_claim_status(claim_id: int, status: str) -> int:
        return execute_query("UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id))
        
    @staticmethod
    def add_claim_history(claim_id: int, officer_id: int, action: str, remarks: str = None) -> int:
        sql = "INSERT INTO claim_history (claim_id, officer_id, action_taken, remarks) VALUES (?, ?, ?, ?)"
        return execute_query(sql, (claim_id, officer_id, action, remarks))
        
    @staticmethod
    def get_claim_history(claim_id: int) -> List[ClaimHistory]:
        return fetch_all("SELECT * FROM claim_history WHERE claim_id = ? ORDER BY action_timestamp ASC", (claim_id,))
        
    @staticmethod
    def get_all_claims() -> List[Claim]:
        sql = """
            SELECT c.*, u.full_name as cust_name, o.full_name as officer_name, mp.policy_name, cp.policy_id 
            FROM claims c 
            JOIN users u ON c.customer_id = u.user_id 
            LEFT JOIN users o ON c.claim_officer_id = o.user_id 
            JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id 
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
        """
        return fetch_all(sql)
        
    @staticmethod
    def get_claim_by_id(claim_id: int) -> Optional[Claim]:
        sql = """
            SELECT c.*, u.full_name as cust_name, o.full_name as officer_name, mp.policy_name, cp.policy_id
            FROM claims c 
            LEFT JOIN users u ON c.customer_id = u.user_id 
            LEFT JOIN users o ON c.claim_officer_id = o.user_id 
            LEFT JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id 
            LEFT JOIN master_policies mp ON cp.policy_id = mp.policy_id 
            WHERE c.claim_id = ?
        """
        return fetch_one(sql, (claim_id,))
