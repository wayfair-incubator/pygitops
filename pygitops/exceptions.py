class PyGitOpsError(Exception):
    """Parent exception class for all errors coming from `pygitops` package."""


class PyGitOpsValueError(PyGitOpsError):
    """The provided argument is invalid."""


class PyGitOpsStagedItemsError(PyGitOpsError):
    """There were no items to stage for commit."""


class PyGitOpsWorkingDirError(PyGitOpsError):
    """There was an error with the filesystem, namely `git.Repo.working_dir` is unexpectedly None."""
