"""Domain exceptions for Causal Intelligence (Phase 5.2)."""


class CausalDomainError(Exception):
    """Base domain exception for causal intelligence."""

    pass


class InvalidTemporalCausalityError(CausalDomainError):
    """Raised when a causal edge violates temporal ordering (source_time > target_time)."""

    pass


class CrossSeriesCausalityError(CausalDomainError):
    """Raised when causal relation spans multiple distinct series."""

    pass


class CausalDepthExceededError(CausalDomainError):
    """Raised when causal traversal exceeds maximum configured depth."""

    pass


class CausalCycleDetectedError(CausalDomainError):
    """Raised when a directed causal cycle is encountered during DAG traversal."""

    pass


class CausalEntityNotFoundError(CausalDomainError):
    """Raised when a target entity or event for causal analysis cannot be found."""

    pass
