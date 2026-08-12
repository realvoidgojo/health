class AppError(Exception):
    """Base class for application errors."""
    pass

class ValidationError(AppError):
    """Raised when input validation fails."""
    pass

class AuthError(AppError):
    """Raised for authentication failures."""
    pass

class NotFoundError(AppError):
    """Raised when an entity is not found."""
    pass

class BusinessRuleError(AppError):
    """Raised when a business rule constraint is violated."""
    pass
