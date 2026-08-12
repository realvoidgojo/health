from typing import List, Optional
from app.core.db.base_repository import execute_query, fetch_one, fetch_all
from app.models.reactivation_request import ReactivationRequest
from app.core.constants import ReactivationStatus

class ReactivationRepository:
    @staticmethod
    def get_pending_request_by_user(user_id: int) -> Optional[ReactivationRequest]:
        return fetch_one("SELECT * FROM reactivation_requests WHERE user_id = ? AND status = ?", (user_id, ReactivationStatus.PENDING))
        
    @staticmethod
    def create_request(user_id: int) -> int:
        return execute_query("INSERT INTO reactivation_requests (user_id) VALUES (?)", (user_id,))
        
    @staticmethod
    def get_all_pending_requests() -> List[ReactivationRequest]:
        sql = """
            SELECT r.*, u.email 
            FROM reactivation_requests r 
            JOIN users u ON r.user_id = u.user_id 
            WHERE r.status = ?
        """
        return fetch_all(sql, (ReactivationStatus.PENDING,))
        
    @staticmethod
    def update_request_status(request_id: int, status: str, admin_remarks: str = None) -> int:
        return execute_query("UPDATE reactivation_requests SET status = ?, admin_remarks = ? WHERE request_id = ?", (status, admin_remarks, request_id))
