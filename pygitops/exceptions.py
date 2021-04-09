class PyGitOpsError(Exception):
    """Parent exception class for all errors coming from `pygitops` package."""


class PyGitOpsValueError(PyGitOpsError):
    """The provided argument is invalid."""


class PyGitOpsStagedItemsError(PyGitOpsError):
    """There were no items to stage for commit."""
