# database.py - Proxy to new architecture to maintain backward compatibility during migration

from app.core.db.connection import get_db_connection, DB_NAME
from app.core.db.base_repository import execute_query, fetch_all, fetch_one
from app.core.security import hash_password
from app.core.validators import validate_email, validate_phone, validate_date
from app.views.console.ui import (
    Colors, print_success, print_error, print_warning, print_info,
    sanitize_input, getpass_asterisk, get_input, display_header, print_card
)

# Backwards compatibility for calculate_age which wasn't originally in database.py
# but we need it since we moved validate_date there.
from app.core.validators import calculate_age
