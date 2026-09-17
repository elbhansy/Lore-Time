"""Application Layer Exception Hierarchy.

Decoupled from FastAPI, HTTP status codes, and database ORM implementations.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    pass


class ResourceNotFound(ApplicationError):
    """Base exception for resource lookup failures."""

    pass


class SeriesNotFound(ResourceNotFound):
    pass


class CharacterNotFound(ResourceNotFound):
    pass


class EntityNotFound(ResourceNotFound):
    pass


class ValidationError(ApplicationError):
    """Base exception for application-level validation failures."""

    pass


class InvalidChapter(ValidationError):
    pass


class ConflictError(ApplicationError):
    """Base exception for concurrency or state conflicts."""

    pass


class InfrastructureError(ApplicationError):
    """Base exception for infrastructure failures (e.g. database)."""

    pass


class DatabaseUnavailable(InfrastructureError):
    pass


class DatabaseTimeout(InfrastructureError):
    pass


class TransactionFailure(InfrastructureError):
    pass
