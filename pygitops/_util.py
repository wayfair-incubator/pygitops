import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from os import PathLike
from pathlib import Path

from filelock import FileLock, Timeout
from git import PushInfo, Repo
from git.exc import InvalidGitRepositoryError

from pygitops.exceptions import PyGitOpsError, PyGitOpsWorkingDirError

_logger = logging.getLogger(__name__)
_lockfile_path = Path("lockfiles")

FILELOCK_ACQUIRE_TIMEOUT_SECONDS = 10


@contextmanager
def lock_repo(repo: Repo) -> Iterator[None]:
    """
    Lock a given repo for use.

    :param repo: The repo to lock on.
    """

    repo_name = os.path.basename(os.path.normpath(repo_working_dir(repo)))
    lockfile_name = str(get_lockfile_path(repo_name))

    lock = FileLock(lockfile_name)
    try:
        with lock.acquire(timeout=FILELOCK_ACQUIRE_TIMEOUT_SECONDS):
            _logger.debug(
                f"Successfully acquired lock: {lockfile_name} for repo: {repo}"
            )
            # yield control to the function using this context manager
            yield
            _logger.debug(f"About to release lock: {lockfile_name} for repo: {repo}")
    except Timeout as err:
        raise PyGitOpsError(
            f"The timeout of {FILELOCK_ACQUIRE_TIMEOUT_SECONDS} seconds was exceeded when attempting to acquire the lockfile: {lockfile_name}"
        ) from err


def checkout_pull_branch(repo: Repo, branch: str, force: bool = False) -> None:
    """
    Pull changes from the specified branch of a repo.

    Will fail if the branch does not exist on the remote
    """

    origin = repo.remotes.origin

    # `origin.refs` might be out of date, this makes local checkout of repo aware of remote branches
    origin.fetch()

    if branch not in repo.heads:
        # handle case where provided branch name isnt a known remote branch
        if branch not in origin.refs:
            raise PyGitOpsError(
                f"The provided branch {branch} does not exist on the remote origin"
            )

        repo.create_head(branch, origin.refs[branch])
        _logger.debug(
            f"[Pull Branch] Create head was successful for repo: {repo}, branch: {branch}"
        )

        repo.heads[branch].set_tracking_branch(origin.refs[branch])
        _logger.debug(
            f"[Pull Branch] Set tracking branch successful for repo: {repo}, branch: {branch}"
        )

    # checkout local `branch` to working tree, optionally discarding changes to the index and working tree
    repo.heads[branch].checkout(force=force)
    _logger.debug(
        f"[Pull Branch] Checkout local branch successful for repo: {repo}, branch: {branch}"
    )

    if force:
        repo.git.clean("-df")
        _logger.debug(
            f"[Pull Branch] Removed untracked files for repo: {repo}, branch: {branch}"
        )

    # pull the changes from the remote branch
    origin.pull(branch)
    _logger.debug(
        f"[Pull Branch] Pull of changes successful for repo: {repo}, branch: {branch}"
    )


def get_lockfile_path(repo_name: str) -> Path:
    """Get a lockfile to lock a git repo."""

    _lockfile_path.mkdir(exist_ok=True)

    return _lockfile_path / f"{repo_name}_lock_file.lock"


def push_error_present(push_info: PushInfo) -> bool:
    """
    Given an instance of `git.remote.PushInfo`, determine if error is present.

    GitPython's remote operations use bitflags to indicate status of operations:
        https://gitpython.readthedocs.io/en/stable/reference.html#git.remote.PushInfo

    Check for presence of the error flag in the returned flags bitmask.
    """
    return bool(push_info.flags & push_info.ERROR)


def is_git_repo(path: Path) -> bool:
    """
    Determine if a given path is a valid git repository.

    :param path: Directory to inspect
    :return: True if the contents of a directory at given path contains a valid git repository
    """
    try:
        _ = Repo(path).git_dir
        return True
    except InvalidGitRepositoryError:
        return False


def repo_working_dir(repo: Repo) -> str | PathLike:
    """
    Between gitpython 3.1.18 and 3.1.29, `git.Repo.working_dir` is now typed as Optional.

    The `os.path` and `pathlib.Path` operations are not typed to support `Optional`.
    Calling this function to access this property will handle cases where `repo.working_dir` is None, although it should never happen in practice.

    :param repo: The repo whose `working_dir` we are interested in.
    :raises PyGitOpsWorkingDirError: Raise error if `working_dir` is unexpectedly None.
    :return str: `working_dir` of the repo
    """
    working_dir = repo.working_dir

    # Can replace with assignment operator when python 3.7 support is dropped
    if working_dir is None:
        raise PyGitOpsWorkingDirError(
            f"The working_dir for repo {repo} is unexpectedly None"
        )

    return working_dir
