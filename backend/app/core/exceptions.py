class NagarikException(Exception):
    """Base exception for all domain errors in Nagarik."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IssueNotFoundException(NagarikException):
    """Raised when an issue is not found in the system."""
    pass


class UnauthorizedActionException(NagarikException):
    """Raised when a user attempts an action they are not permitted to do."""
    pass


class DuplicateIssueException(NagarikException):
    """Raised when a duplicate issue action/submission is detected."""
    pass
