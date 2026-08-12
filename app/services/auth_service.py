from typing import Dict, Any, Optional
from app.repositories.user_repository import UserRepository
from app.repositories.reactivation_repository import ReactivationRepository
from app.core.security import hash_password
from app.core.validators import validate_email, validate_phone, validate_date
from app.core.exceptions import AuthError, ValidationError, BusinessRuleError

class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> Dict[str, Any]:
        """Authenticates user. Raises exceptions for various failure states."""
        hashed = hash_password(password)
        user = UserRepository.get_by_email_and_password(email, hashed)
        
        if not user:
            raise AuthError("Invalid email or password.")
            
        if user['is_deleted']:
            raise BusinessRuleError("Account is deleted. Please request reactivation.")
            
        if not user['is_active']:
            raise BusinessRuleError("Account is inactive. Please contact administrator.")
            
        return user

    @staticmethod
    def register_customer(full_name: str, email: str, password: str, phone: str, date_of_birth: str) -> int:
        if not validate_email(email):
            raise ValidationError("Invalid email format.")
        
        if not validate_phone(phone):
            raise ValidationError("Invalid phone format.")
            
        if not validate_date(date_birth := date_of_birth):
            raise ValidationError("Invalid date format.")
            
        if UserRepository.get_by_email(email):
            raise ValidationError("An account with this email already exists.")
            
        # Assign random agent
        agent = UserRepository.get_random_active_agent()
        agent_id = agent['user_id'] if agent else None
        
        hashed = hash_password(password)
        return UserRepository.create_customer(full_name, email, hashed, phone, date_of_birth, agent_id)

    @staticmethod
    def request_reactivation(email: str, password: str) -> None:
        hashed = hash_password(password)
        user = UserRepository.get_by_email_and_password(email, hashed)
        
        if not user:
            raise AuthError("Invalid email or password.")
            
        if not user['is_deleted']:
            raise BusinessRuleError("Account is not deleted.")
            
        existing_request = ReactivationRepository.get_pending_request_by_user(user['user_id'])
        if existing_request:
            raise BusinessRuleError("A reactivation request is already pending.")
            
        ReactivationRepository.create_request(user['user_id'])
