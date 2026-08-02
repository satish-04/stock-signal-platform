"""Custom exceptions for stock signal app."""


class AppError(Exception):
    """Base application exception."""
    pass


class ConfigError(AppError):
    """Configuration error."""
    pass


class DatabaseError(AppError):
    """Database-related errors."""
    pass


class MarketDataError(AppError):
    """Market data retrieval errors."""
    pass


class BrokerError(AppError):
    """Broker API errors."""
    pass


class IBAPIError(BrokerError):
    """IBKR API specific errors."""
    pass


class AIError(AppError):
    """AI service errors."""
    pass


class OrderExecutionError(AppError):
    """Order execution errors."""
    pass


class RiskViolationError(AppError):
    """Risk limit violations."""
    pass


class ValidationError(AppError):
    """Data validation errors."""
    pass


class NotFoundError(AppError):
    """Resource not found."""
    pass


class ConflictError(AppError):
    """Conflict error (e.g., duplicate resource)."""
    pass


class UnauthorizedError(AppError):
    """Unauthorized access error."""
    pass


class TimeoutError(AppError):
    """Timeout errors."""
    pass


class RateLimitError(AppError):
    """Rate limit exceeded."""
    pass


def handle_error(error: Exception) -> dict:
    """
    Handle error and return standardized response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Dictionary with error details for API response
    """
    if isinstance(error, AppError):
        return {
            "error": True,
            "error_type": error.__class__.__name__,
            "message": str(error),
        }
    else:
        return {
            "error": True,
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred",
        }
