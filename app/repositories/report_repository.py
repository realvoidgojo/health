from typing import Tuple
from app.core.db.base_repository import fetch_one
from app.core.constants import PolicyStatus, ClaimStatus

class ReportRepository:
    @staticmethod
    def get_active_policies_count() -> int:
        row = fetch_one("SELECT COUNT(*) as count FROM customer_policies WHERE status = ?", (PolicyStatus.ACTIVE,))
        return row['count'] if row else 0
        
    @staticmethod
    def get_expired_policies_count() -> int:
        row = fetch_one("SELECT COUNT(*) as count FROM customer_policies WHERE status = ?", (PolicyStatus.EXPIRED,))
        return row['count'] if row else 0
        
    @staticmethod
    def get_approved_claims_stats() -> Tuple[int, float]:
        row = fetch_one("SELECT COUNT(*) as count, SUM(claim_amount) as total FROM claims WHERE status = ?", (ClaimStatus.APPROVED,))
        if row and row['count'] > 0:
            return row['count'], float(row['total'] or 0)
        return 0, 0.0
        
    @staticmethod
    def get_rejected_claims_stats() -> Tuple[int, float]:
        row = fetch_one("SELECT COUNT(*) as count, SUM(claim_amount) as total FROM claims WHERE status = ?", (ClaimStatus.REJECTED,))
        if row and row['count'] > 0:
            return row['count'], float(row['total'] or 0)
        return 0, 0.0

    @staticmethod
    def get_active_policies_report():
        sql = """
            SELECT cp.customer_policy_id, u.full_name as customer_name, mp.policy_name, cp.start_date, cp.expiry_date
            FROM customer_policies cp
            JOIN users u ON cp.customer_id = u.user_id
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
            WHERE cp.status = ?
        """
        from app.core.db.base_repository import fetch_all
        return fetch_all(sql, (PolicyStatus.ACTIVE,))

    @staticmethod
    def get_expired_policies_report():
        sql = """
            SELECT cp.customer_policy_id, u.full_name as customer_name, mp.policy_name, cp.expiry_date
            FROM customer_policies cp
            JOIN users u ON cp.customer_id = u.user_id
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
            WHERE cp.status = ?
        """
        from app.core.db.base_repository import fetch_all
        return fetch_all(sql, (PolicyStatus.EXPIRED,))

    @staticmethod
    def get_approved_claims_report():
        sql = """
            SELECT c.claim_id, u.full_name as customer_name, mp.policy_name, c.claim_amount, c.updated_at as approval_date
            FROM claims c
            JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id
            JOIN users u ON cp.customer_id = u.user_id
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
            WHERE c.status = ?
        """
        from app.core.db.base_repository import fetch_all
        return fetch_all(sql, (ClaimStatus.APPROVED,))

    @staticmethod
    def get_rejected_claims_report():
        sql = """
            SELECT c.claim_id, u.full_name as customer_name, mp.policy_name, c.claim_amount, c.officer_remarks as reason
            FROM claims c
            JOIN customer_policies cp ON c.customer_policy_id = cp.customer_policy_id
            JOIN users u ON cp.customer_id = u.user_id
            JOIN master_policies mp ON cp.policy_id = mp.policy_id
            WHERE c.status = ?
        """
        from app.core.db.base_repository import fetch_all
        return fetch_all(sql, (ClaimStatus.REJECTED,))

    @staticmethod
    def get_agent_performance_report():
        sql = """
            SELECT 
                u.user_id as agent_id, 
                u.full_name as agent_name,
                COUNT(cp.customer_policy_id) as total_policies_handled,
                SUM(CASE WHEN cp.status = 'ACTIVE' THEN 1 ELSE 0 END) as active_policies
            FROM users u
            LEFT JOIN customer_policies cp ON u.user_id = cp.assigned_agent_id
            WHERE u.role = 'POLICY_AGENT' AND u.is_deleted = 0
            GROUP BY u.user_id, u.full_name
        """
        from app.core.db.base_repository import fetch_all
        return fetch_all(sql)
