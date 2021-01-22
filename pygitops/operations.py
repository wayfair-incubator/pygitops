import logging
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional

from filelock import FileLock
from git import Actor, GitError, Repo

from pygitops._constants import GITHUB_PUBLIC_DOMAIN_NAME, KNOWN_DEFAULT_BRANCHES
from pygitops._util import checkout_pull_branch as _checkout_pull_branch
from pygitops._util import get_lockfile_path as _get_lockfile_path
from pygitops._util import lock_repo as _lock_repo
from pygitops._util import push_error_present as _push_error_present
from pygitops.exceptions import (
    PyGitOpsError,
    PyGitOpsStagedItemsError,
    PyGitOpsValueError,
)
from pygitops.types import GitBranchType, GitDefaultBranch, PathOrStr

_logger = logging.getLogger(__name__)


def stage_commit_push_changes(
    repo: Repo,
    branch: GitBranchType,
    actor: Actor,
    commit_message: str,
    items_to_stage: Optional[List[Path]] = None,
) -> None:
    """
    Handles the logic of persisting filesystem changes to a local repository via a commit to a feature branch.

    This includes staging, committing, and pushing the local changes.

    :param repo: Repository object.
    :param branch: Feature branch from which changes will be committed and pushed.
    :param actor: The Github actor with which to perform the commit operation.
    :param commit_message: Text to be used as the commit message.
    :param items_to_stage: List of files and directories that will be staged for commit, if None will include all changes.
    :raises PyGitOpsStagedItemsError: There were no items to stage.
    :raises PyGitOpsError: There was an error staging, committing, or pushing code.
    """

    branch_name = _get_branch_name(repo, branch)

    index = repo.index
    workdir_path = Path(repo.working_dir)

    if items_to_stage is None:
        untracked_file_paths = [Path(f) for f in repo.untracked_files]
        items_to_stage = untracked_file_paths + [
            Path(f.a_path) for f in index.diff(None)
        ]

    if not items_to_stage:
        raise PyGitOpsStagedItemsError(
            "There are no items to stage, cannot perform commit operation"
        )

    # stage and commit changes using the provided actor.
    for item in items_to_stage:
        full_path = workdir_path / item
        index.add(str(item)) if full_path.exists() else index.remove(str(item), r=True)
    index.commit(commit_message, author=actor, committer=actor)

    _logger.debug(f"Successfully made commit to repository: {repo}")

    # push changes to the remote branch
    origin = repo.remotes.origin
    push_info = origin.push(branch_name)[0]

    _logger.debug(
        f"Commit pushed to remote branch: {branch_name}, push info: {push_info}"
    )

    if _push_error_present(push_info):
        raise PyGitOpsError(
            f"Unable to push to branch {branch_name} of new repo: {repo}"
        )


@contextmanager
def feature_branch(repo: Repo, branch: GitBranchType) -> Iterator[None]:
    """
    Checkout the desired feature branch.

    Return to the default branch when context is exited.

    The main responsibility of this context manager is to limit concurrent
    operations on the local filesystem via the FileLock.

    Local git commit operations in particular should leverage this behavior.

    *** Assumes default branch is checked out, otherwise raises PyGitOpsError ***

    :param repo: Repository object
    :param branch: GitBranchType object indicating the branch we would like to checkout
    :raises PyGitOpsError: There was an error performing the feature branch operation.
    """

    branch_name = _get_branch_name(repo, branch)
    default_branch = get_default_branch(repo)

    untracked_files = repo.untracked_files
    if untracked_files:
        raise PyGitOpsError(
            f"We cannot checkout a feature branch when there are unstaged changes in your current branch: {untracked_files}"
        )

    active_branch = repo.active_branch
    if active_branch != repo.heads[default_branch]:
        raise PyGitOpsError(
            f"We can only checkout feature branches originating from the default branch: {default_branch}. Current branch is: {active_branch.name}"
        )

    _logger.debug(
        f"About to invoke `_lock_repo` for repo: {repo}, branch name: {branch_name}"
    )

    # lock the following operation such that the process of updating default branch,
    # checking out a feature branch, applying changes, and moving back to default branch never occurs concurrently
    with _lock_repo(repo):

        _logger.debug(
            f"Successfully using repository: {repo}, branch_name: {branch_name}"
        )

        # before creating a feature branch, checkout and update the default branch of the repository
        # helpful in the case where a failed process clears the FileLock, but leaves the repo on a feature branch
        origin = repo.remotes.origin
        # `origin.refs` might be out of date, this makes local checkout of repo aware of remote branches
        origin.fetch()

        # Handle the case where the remote is a bare repository with no commit history.
        # When there is no commit history, there is no default branch
        if default_branch in origin.refs:
            _checkout_pull_branch(repo, default_branch)
            _logger.debug(
                f"Successfully updated {default_branch} branch of repo: {repo}"
            )

        if branch_name != default_branch:
            # create and checkout a local feature branch
            feature_branch = repo.create_head(branch_name)
            feature_branch.checkout()

            _logger.debug(
                f"Successfully checked out feature branch: {branch_name} for repository: {repo}"
            )

        # give control back to call of this context manager
        try:
            yield
        finally:
            # move back to the repo's default branch when the `feature_branch` context is exited
            repo.heads[default_branch].checkout()
            _logger.debug(
                f"Successfully moved back to {default_branch} branch for repository: {repo} after using feature branch"
            )


def build_github_repo_url(
    service_account_name: str,
    service_account_token: str,
    repo_namespace: str,
    repo_name: str,
    domain_name: str = GITHUB_PUBLIC_DOMAIN_NAME,
) -> str:
    """
    Build github repo_url with the intention of providing as the `repo_url` argument to `get_updated_repo`.
    This factory function is specific to github, and might not support url schemas of different git services.

    :param service_account_name: Name of the Github service account used to clone repository.
    :param service_account_token: Raw token associated with the provided Github service account name.
    :param repo_namespace: The namespace of the target repository.
    :param repo_name: The name of the target repository.
    :param domain_name: Github domain, allows us to point to instances other than public Github.
    """

    return f"https://{service_account_name}:{service_account_token}@{domain_name}/{repo_namespace}/{repo_name}.git"


def get_updated_repo(
    repo_url: str, clone_dir: PathOrStr, repo_name: str, **kwargs
) -> Repo:
    """
    Clone the default branch of the target repository, returning a repo object.

    If repo is already present, we will pull in the latest changes to the default branch of the repo.

    :param repo_url: URL of the Github repository to be cloned.
    :param clone_dir: The root directory where repositories are cloned.
    :param repo_name: The name of the repository to be cloned.
    :raises PyGitOpsError: There was an error cloning the repository.
    """

    sa_token_regex = "https://.+?:.+?@"
    sa_token_replace_term = "https://***:***@"

    # make sure it's actually a Path if our user passed a str
    clone_dir = Path(clone_dir)

    dest_repo_path = clone_dir / repo_name
    git_lockfile_path = _get_lockfile_path(repo_name)

    # Lock the following operation such that only one process will attempt to clone the repo at a time.
    with FileLock(str(git_lockfile_path)):
        try:
            # only clone the project if the local checkout doesnt exist
            if dest_repo_path.is_dir():
                repo = Repo(dest_repo_path)
                # pull down latest changes from `branch` if provided in kwargs, deferring to repo default branch
                branch = kwargs.get("branch") or get_default_branch(repo)
                _checkout_pull_branch(repo, branch)
                return repo

            return Repo.clone_from(repo_url, dest_repo_path, **kwargs)
        except GitError as e:
            clean_repo_url = re.sub(sa_token_regex, sa_token_replace_term, repo_url)
            scrubbed_error_message = re.sub(
                sa_token_regex, sa_token_replace_term, str(e)
            )
            raise PyGitOpsError(
                f"Error cloning repo {clean_repo_url} into destination path {dest_repo_path}: {scrubbed_error_message}"
            ) from e


def get_default_branch(repo: Repo) -> str:
    """
    Get the default branch of the provided repository.

    Although Git itself does not have a concept of default branches, a default branch on a GitHub repository maps directly to the HEAD symbolic ref.
    Pull in remote branches and update local head refs pointing to the remote repository.
    We expect the HEAD ref to match a particular pattern that we regex against.

    :param repo: git.Repo instance.
    :return: string representing name of default branch.
    """

    git_ref_regex = r"refs\/remotes\/origin\/(\w*)"
    symbolic_ref_head = "refs/remotes/origin/HEAD"

    # local repo should be aware of branch objects prior to running the `set-head` command, where an unknown branch might be present
    repo.remotes.origin.fetch()

    # update HEAD pointer before querying local state
    repo.git.remote(["set-head", "-a", "origin"])

    # query local state for the HEAD pointer
    default_ref = repo.git.symbolic_ref(symbolic_ref_head)

    match = re.match(git_ref_regex, default_ref)
    if not match:
        raise PyGitOpsError(
            f"None of the symbolic refs using {symbolic_ref_head} matched the regex: {git_ref_regex}"
        )

    expected_position = 1
    try:
        return match.group(expected_position)
    except IndexError:
        raise PyGitOpsError(
            f"The match object did not have a group in position {expected_position}"
        )


def _get_branch_name(repo: Repo, branch: GitBranchType) -> str:
    """
    Get the string version of the provided branch name.

    Helpful for resolving non string representations of git branches.

    :param repo: git.Repo instance
    :param branch: branch to resolve, either a plain string or a value allowable by the `GitBranchType`
    :return: string representing name of default branch.
    """

    if isinstance(branch, str):
        if branch in KNOWN_DEFAULT_BRANCHES:
            raise PyGitOpsValueError(
                f"The branch value of {branch} cannot be provided directly. Please instead provide `pygitops.GIT_DEFAULT_BRANCH` to indicate a reference to the default branch of the repository."
            )
        return branch
    elif isinstance(branch, GitDefaultBranch):
        return get_default_branch(repo)

    raise PyGitOpsValueError(
        f"The provided branch {branch} is not a valid GitBranchType"
    )
