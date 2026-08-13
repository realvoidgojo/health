from typing import List, Optional
from app.core.db.base_repository import execute_query, fetch_one, fetch_all
from app.models.user import User
from app.core.constants import Role

class UserRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        
    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        
    @staticmethod
    def get_by_email_and_password(email: str, hashed_pw: str) -> Optional[User]:
        return fetch_one("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_pw))
        
    @staticmethod
    def get_users_by_role(role: str) -> List[User]:
        return fetch_all("SELECT * FROM users WHERE role = ? AND is_deleted = 0", (role,))
        
    @staticmethod
    def get_customers_by_agent(agent_id: int) -> List[User]:
        return fetch_all("SELECT * FROM users WHERE assigned_agent_id = ? AND is_deleted = 0", (agent_id,))
        
    @staticmethod
    def get_all_users() -> List[User]:
        return fetch_all("SELECT user_id, full_name, email, role, is_active, is_deleted, assigned_agent_id, phone, date_of_birth, created_at FROM users")
        
    @staticmethod
    def get_staff_members() -> List[User]:
        return fetch_all(
            "SELECT * FROM users "
            "WHERE role IN (?, ?) AND is_deleted = 0", 
            (Role.POLICY_AGENT, Role.CLAIM_OFFICER)
        )
        
    @staticmethod
    def get_random_active_agent() -> Optional[User]:
        return fetch_one(
            "SELECT user_id FROM users WHERE role = ? AND is_active = 1 ORDER BY RANDOM() LIMIT 1", 
            (Role.POLICY_AGENT,)
        )
        
    @staticmethod
    def create_customer(full_name: str, email: str, password: str, phone: str, date_of_birth: str, assigned_agent_id: int) -> int:
        sql = """
            INSERT INTO users (full_name, email, password, phone, date_of_birth, role, assigned_agent_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return execute_query(sql, (full_name, email, password, phone, date_of_birth, Role.CUSTOMER, assigned_agent_id))
        
    @staticmethod
    def create_staff(full_name: str, email: str, password: str, phone: str, date_of_birth: str, role: str) -> int:
        sql = """
            INSERT INTO users (full_name, email, password, phone, date_of_birth, role) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return execute_query(sql, (full_name, email, password, phone, date_of_birth, role))
        
    @staticmethod
    def update_field(user_id: int, field: str, value: any) -> int:
        # Safe because field is validated in service layer
        return execute_query(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
        
    @staticmethod
    def soft_delete(user_id: int) -> int:
        return execute_query("UPDATE users SET is_deleted = 1, is_active = 0 WHERE user_id = ?", (user_id,))
        
    @staticmethod
    def reactivate(user_id: int) -> int:
        return execute_query("UPDATE users SET is_deleted = 0, is_active = 1 WHERE user_id = ?", (user_id,))
