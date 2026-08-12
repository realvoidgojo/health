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
    """Validates date string format YYYY-MM-DD."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
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
