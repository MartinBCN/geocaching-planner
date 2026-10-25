"""Framework-free domain errors. The API layer maps them to HTTP responses."""


class DomainError(Exception):
    """Base class for domain failures."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""


class ConflictError(DomainError):
    """The request conflicts with the current state."""


class UpstreamUnavailableError(DomainError):
    """An external dependency is unavailable."""
