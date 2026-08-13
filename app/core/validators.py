import re
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validates email format."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validates phone format to be 10 digits and optional +91 prefix."""
    pattern = r"^(?:\+91[\-\s]?)?[6-9]\d{9}$"
    return bool(re.match(pattern, phone))

def validate_date(date_str: str) -> bool:
    """Validates date string format YYYY-MM-DD and basic bounds."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        age = (datetime.now() - dt).days / 365
        # Must not be in future, and age must be < 120
        if dt > datetime.now() or age > 120:
            return False
        return True
    except ValueError:
        return False

def calculate_age(dob: str) -> int:
    """Calculates age based on YYYY-MM-DD string."""
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        return (datetime.now() - dob_date).days // 365
    except Exception:
        return 30  # Default fallback

def validate_password(password: str) -> bool:
    """Validates password strength (min 8 chars, at least one letter and one number)."""
    if len(password) < 8:
        return False
    if not any(char.isalpha() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    return True
