import shutil
import unittest.mock as mock
from pathlib import Path

import pytest
from filelock import Timeout
from git import PushInfo, Repo

from pygitops._util import (
    _lockfile_path,
    checkout_pull_branch,
    get_lockfile_path,
    is_git_repo,
    lock_repo,
    push_error_present,
)
from pygitops.exceptions import PyGitOpsError

SOME_REPO_NAME = "some-repo-name"


@pytest.fixture(scope="session", autouse=True)
def _teardown():
    """This function removes the lockfiles directory after all tests are done."""
    yield  # let tests run
    shutil.rmtree(_lockfile_path)


@pytest.mark.parametrize(
    ("expected_response", "flags"),
    [(True, PushInfo.ERROR), (True, PushInfo.ERROR + 1), (False, PushInfo.ERROR - 1)],
)
def test_push_error_present(expected_response, flags):
    """
    Validate push_error_present reports an issue correctly.

    Given some integer representing the push flags, validate the reporting of each
    push error scenario.
    """

    push_info = PushInfo(flags, "", "", "")
    assert push_error_present(push_info) == expected_response


def test_lock_repo__filelock_acquire_timeout__raises_pygitops_error(mocker):
    class FakeFileLock:
        def acquire(self, timeout: int):
            raise Timeout("some-file")

    repo_mock = mocker.Mock(working_dir=f"some-repo-namespace/{SOME_REPO_NAME}")
    mocker.patch("pygitops._util.FileLock", return_value=FakeFileLock())

    with pytest.raises(PyGitOpsError):
        with lock_repo(repo_mock):
            pass


@pytest.mark.parametrize("path_exists", (True, False))
def test_get_lockfile_path__expected_path_returned(mocker, tmp_path, path_exists):

    mocker.patch("pygitops._util._lockfile_path", new=tmp_path)

    if path_exists:
        (tmp_path / SOME_REPO_NAME).mkdir()

    assert get_lockfile_path(SOME_REPO_NAME) == Path(
        f"{tmp_path}/{SOME_REPO_NAME}_lock_file.lock"
    )


def test_get_lockfile_path__lockfile_dir_dne__lockfile_dir_created(mocker, tmp_path):

    some_lockfile_dir = "some-lockfile-dir"
    mocker.patch("pygitops._util._lockfile_path", new=tmp_path / some_lockfile_dir)

    assert get_lockfile_path(SOME_REPO_NAME) == Path(
        f"{tmp_path}/{some_lockfile_dir}/{SOME_REPO_NAME}_lock_file.lock"
    )


def test_pull_branch__head_present__head_not_created(mocker):
    """
    In the case where checkout_pull_branch() is invoked, and a head for the specified branch is present,
    the operation should not create head nor set the tracking branch
    """

    branch = "test_branch"

    test_branch_head_mock = mocker.Mock()

    origin_mock = mocker.Mock(refs={branch: mock.ANY})
    create_head_mock = mocker.Mock()

    repo = mocker.Mock(
        heads={branch: test_branch_head_mock},
        remotes=mocker.Mock(origin=origin_mock),
        create_head=create_head_mock,
    )

    checkout_pull_branch(repo, branch)

    create_head_mock.assert_not_called()
    test_branch_head_mock.assert_not_called()


def test_pull_branch__head_not_present__head_created(mocker):
    """
    In the case where checkout_pull_branch() is invoked, and a head is not present,
    the operation should create the head and set the tracking branch
    """

    heads = {}
    branch = "test_branch"
    ref = mock.ANY

    test_branch_head_mock = mocker.Mock()

    def _create_head(*args):
        """
        Invoked as a side effect of the `create_head_mock`.
        Updates state of `heads` such that tracking branch registration succeeds
        """
        heads[branch] = test_branch_head_mock

    origin_mock = mocker.Mock(refs={branch: ref})
    create_head_mock = mocker.Mock(side_effect=_create_head)

    repo = mocker.Mock(
        heads=heads,
        remotes=mocker.Mock(origin=origin_mock),
        create_head=create_head_mock,
    )

    checkout_pull_branch(repo, branch)

    create_head_mock.assert_called_once_with(branch, ref)
    test_branch_head_mock.set_tracking_branch.assert_called_once()


def test_pull_branch__branch_not_in_refs__raises_pygitops_error(mocker):
    """
    In the case where the provided branch is not in the list of remote refs, A GitOperationError should be raised
    """

    origin_mock = mocker.Mock(refs={})

    repo = mocker.Mock(heads={}, remotes=mocker.Mock(origin=origin_mock))

    with pytest.raises(PyGitOpsError):
        checkout_pull_branch(repo, "test_branch")


def test_is_git_repo__not_a_git_repo__returns_false(tmp_path):
    assert is_git_repo(tmp_path) is False


def test_is_git_repo__is_a_git_repo__returns_true(tmp_path):
    Repo.init(tmp_path)
    assert is_git_repo(tmp_path)
