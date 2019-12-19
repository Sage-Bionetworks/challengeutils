"""
Define Python user-defined exceptions
"""


class Error(Exception):
    """Base class for other exceptions"""
    pass


class InvalidSubmission(Error):
    """Raised when the submission is invalid"""
    pass
