"""Repository-specific error types."""


class ValidationError(ValueError):
    """Raised when supplied data or configuration is invalid."""


class NotFoundError(LookupError):
    """Raised when a required object cannot be found."""


class ConflictError(RuntimeError):
    """Raised when an operation conflicts with the configured environment."""
