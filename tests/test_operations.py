import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PosixPath

import pytest
from git import Actor, GitCommandError, GitError, Repo

from pygitops._constants import GIT_BRANCH_MAIN, GIT_BRANCH_MASTER
from pygitops._util import checkout_pull_branch
from pygitops.exceptions import PyGitOpsError, PyGitOpsStagedItemsError
from pygitops.operations import (
    feature_branch,
    get_default_branch,
    get_updated_repo,
    stage_commit_push_changes,
)

SOME_ACTOR = Actor("some-user", "some-user@company.com")
SOME_COMMIT_MESSAGE = "some-commit-message"
SOME_CONTENT_FILENAME = "foo.txt"
SOME_CHANGES = "some changes"
SOME_INITIAL_CONTENT = "foobar"
SOME_NEW_CONTENT = "newbar"
SOME_FEATURE_BRANCH = "test_branch"
SOME_DEFAULT_BRANCH_NAME = "some_default_branch_name"
SOME_SERVICE_ACCOUNT_NAME = "some-service-account-name"
SOME_SERVICE_ACCOUNT_TOKEN = "test_cred_123"

SOME_GITHUB_DOMAIN_NAME = "some-github-domain-name"
SOME_REPO_NAMESPACE = "test_namespace"
SOME_REPO_NAME = "some-repo-name"
SOME_CLONE_REPO_URL = f"https://{SOME_SERVICE_ACCOUNT_NAME}:{SOME_SERVICE_ACCOUNT_TOKEN}@{SOME_GITHUB_DOMAIN_NAME}/{SOME_REPO_NAMESPACE}/{SOME_REPO_NAME}.git"
SOME_CLONE_PATH = Path("foo")
SOME_LOCAL_REPO_NAME = "local"
SOME_HEAD_REF = f"refs/remotes/origin/{GIT_BRANCH_MASTER}"

SOME_OTHER_FILENAME = "SOME_OTHER_FILENAME.txt"
SOME_BRANCH_NAME = "some-branch-name"
SOME_OTHER_BRANCH_NAME = "some-other-branch-name"
SOME_CONTENT = "some-content"
SOME_MODIFY_FILE_DIFF = "diff --git a/foo.txt b/foo.txt\nindex 5f0c613..74cd6e7 100644\n--- a/foo.txt\n+++ b/foo.txt\n@@ -1 +1 @@\n-some changes\n\\ No newline at end of file\n+some-content\n\\ No newline at end of file"
SOME_DELETE_FILE_DIFF = "diff --git a/foo.txt b/foo.txt\ndeleted file mode 100644\nindex 5f0c613..0000000\n--- a/foo.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-some changes\n\\ No newline at end of file"
SOME_NEW_FILE_DIFF = "diff --git a/SOME_OTHER_FILENAME.txt b/SOME_OTHER_FILENAME.txt\nnew file mode 100644\nindex 0000000..e69de29"


@dataclass
class MultipleTestingRepos:
    """
    Model encapsulating the multi-repo setup used when testing git operations.

    :attr remote_repo: The bare remote repo.
    :attr local_repo: A local repo where state will be asserted.
    :attr cloned_repo: A cloned repo needed to push to bare remote to test _checkout_pull_branch.
    """

    remote_repo: Repo
    local_repo: Repo
    cloned_repo: Repo


def test_stage_commit_push_changes__push_failure__raises_pygitops_error(
    mocker, tmp_path
):
    mocker.patch("pygitops.operations._push_error_present", return_value=True)
    repos = _initialize_multiple_empty_repos(tmp_path)
    cloned_repo = repos.cloned_repo

    with feature_branch(cloned_repo, SOME_FEATURE_BRANCH):
        # Write to remote from the clone, then pull from local
        test_file_path = Path(cloned_repo.working_dir) / SOME_CONTENT_FILENAME
        test_file_path.write_text(SOME_INITIAL_CONTENT)

        with pytest.raises(PyGitOpsError, match=SOME_FEATURE_BRANCH):
            stage_commit_push_changes(
                cloned_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
            )


def _delete_existing_file(local_repo: Repo, filename: str) -> None:
    test_second_file_path = Path(local_repo.working_dir) / filename
    test_second_file_path.unlink()


def _modify_existing_file(local_repo: Repo, filename: str, content: str) -> None:
    test_file_path = Path(local_repo.working_dir) / filename
    test_file_path.write_text(content)


def _add_new_file(local_repo: Repo, filename: str) -> None:
    test_other_file_path = Path(local_repo.working_dir) / filename
    test_other_file_path.touch()


@pytest.mark.parametrize(
    (
        "some_source_modifier",
        "some_source_modifier_inputs",
        "some_other_source_modifier",
        "some_other_source_modifier_inputs",
        "some_result",
        "some_other_result",
    ),
    [
        (
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            SOME_MODIFY_FILE_DIFF,
            SOME_MODIFY_FILE_DIFF,
        ),
        (
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            SOME_DELETE_FILE_DIFF,
            SOME_DELETE_FILE_DIFF,
        ),
        (
            _add_new_file,
            [SOME_OTHER_FILENAME],
            _add_new_file,
            [SOME_OTHER_FILENAME],
            SOME_NEW_FILE_DIFF,
            SOME_NEW_FILE_DIFF,
        ),
        (
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            _add_new_file,
            [SOME_OTHER_FILENAME],
            SOME_MODIFY_FILE_DIFF,
            SOME_NEW_FILE_DIFF,
        ),
        (
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            _modify_existing_file,
            [SOME_CONTENT_FILENAME, SOME_CONTENT],
            SOME_DELETE_FILE_DIFF,
            SOME_MODIFY_FILE_DIFF,
        ),
        (
            _add_new_file,
            [SOME_OTHER_FILENAME],
            _delete_existing_file,
            [SOME_CONTENT_FILENAME],
            SOME_NEW_FILE_DIFF,
            SOME_DELETE_FILE_DIFF,
        ),
    ],
)
def test_feature_branch_context_manager__add_new_file_in_different_branches__clean_up_successfully(
    tmp_path,
    some_source_modifier,
    some_source_modifier_inputs,
    some_other_source_modifier,
    some_other_source_modifier_inputs,
    some_result,
    some_other_result,
):
    local_repo = _initialize_multiple_empty_repos(tmp_path).local_repo
    some_branch_name = SOME_BRANCH_NAME
    with feature_branch(local_repo, some_branch_name):
        some_source_modifier(local_repo, *some_source_modifier_inputs)
        some_diff = _get_diff(local_repo)
        assert some_diff == some_result
    some_other_branch_name = SOME_OTHER_BRANCH_NAME
    with feature_branch(local_repo, some_other_branch_name):
        some_other_source_modifier(local_repo, *some_other_source_modifier_inputs)
        some_other_diff = _get_diff(local_repo)
        assert some_other_diff == some_other_result


def test_stage_commit_push_changes__add_new_file__change_persisted(tmp_path):
    """
    Configure 'local' and 'remote' repositories with initial content.

    After generating new content in a local feature branch,
    verifies that `stage_commit_push_changes` function pushes new content to remote.
    """

    repos = _initialize_multiple_empty_repos(tmp_path)
    remote_repo = repos.remote_repo
    local_repo = repos.local_repo

    with feature_branch(local_repo, SOME_FEATURE_BRANCH):

        test_file_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME
        test_file_path.write_text(SOME_INITIAL_CONTENT)

        # act, asserting expected state before and after operation
        with _assert_branch_state_stage_commit_push_changes__file_added(
            remote_repo, local_repo
        ):
            stage_commit_push_changes(
                local_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
            )

            # checkout `SOME_FEATURE_BRANCH` so that `_assert_branch_state_stage_commit_push_changes__file_added` compares correct commits
            remote_repo.heads[SOME_FEATURE_BRANCH].checkout()


def test_stage_commit_push_changes__remove_old_file__change_persisted(tmp_path):
    """
    Configure 'local' and 'remote' repositories with initial content.

    After generating new content in a local feature branch,
    verifies that `stage_commit_push_changes` function pushes new content to remote.
    """

    repos = _initialize_multiple_empty_repos(tmp_path)
    remote_repo = repos.remote_repo
    local_repo = repos.local_repo
    cloned_repo = repos.cloned_repo

    with feature_branch(cloned_repo, SOME_FEATURE_BRANCH):
        test_file_path = Path(cloned_repo.working_dir) / SOME_CONTENT_FILENAME
        test_file_path.write_text(SOME_INITIAL_CONTENT)

        stage_commit_push_changes(
            cloned_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
        )

        # Pull file on remote (pushed from clone) into local repo
        checkout_pull_branch(local_repo, SOME_FEATURE_BRANCH)

        # Assert expected state before and after operation
        with _assert_branch_state_stage_commit_push_changes__file_removed(
            remote_repo, local_repo
        ):
            removal_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME
            removal_path.unlink()

            # Commit the removal
            stage_commit_push_changes(
                local_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
            )

            # checkout `SOME_FEATURE_BRANCH` so that `_assert_branch_state_stage_commit_push_changes__file_added` compares correct commits
            remote_repo.heads[SOME_FEATURE_BRANCH].checkout()


def test_stage_commit_push_changes__with_staged_files__adds_only_requested_file(
    tmp_path,
):
    """
    Configure 'local' and 'remote' repositories with initial content.

    After generating new content in a local feature branch,
    verifies that `stage_commit_push_changes` function pushes only the files specified to remote.
    """

    repos = _initialize_multiple_empty_repos(tmp_path)
    remote_repo = repos.remote_repo
    local_repo = repos.local_repo
    other_file = "my_test_file.txt"

    with feature_branch(local_repo, SOME_FEATURE_BRANCH):

        test_file_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME
        test_file_path.write_text(SOME_INITIAL_CONTENT)
        other_file_path = Path(local_repo.working_dir) / other_file
        other_file_path.write_text("other test content")

        # act, asserting expected state before and after operation
        with _assert_branch_state_stage_commit_push_changes__file_added(
            remote_repo, local_repo
        ):
            stage_commit_push_changes(
                local_repo,
                SOME_FEATURE_BRANCH,
                SOME_ACTOR,
                SOME_COMMIT_MESSAGE,
                [test_file_path],
            )

            # checkout `SOME_FEATURE_BRANCH` so that `_assert_branch_state_stage_commit_push_changes__file_added` compares correct commits
            remote_repo.heads[SOME_FEATURE_BRANCH].checkout()

        # Assert the "other file" is still untracked
        assert [other_file] == local_repo.untracked_files


def test_stage_commit_push_changes__no_files_to_stage__raises_pygitops_error(tmp_path):

    repos = _initialize_multiple_empty_repos(tmp_path)
    local_repo = repos.local_repo

    with pytest.raises(PyGitOpsStagedItemsError):
        with feature_branch(local_repo, SOME_FEATURE_BRANCH):
            stage_commit_push_changes(
                local_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
            )


def test_stage_commit_push_changes__force_push_flag__changes_pushed(tmp_path):
    repos = _initialize_multiple_empty_repos(tmp_path)
    local_repo = repos.local_repo
    with feature_branch(local_repo, SOME_FEATURE_BRANCH):
        test_file_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME
        test_file_path.write_text("content one")
        stage_commit_push_changes(
            local_repo, SOME_FEATURE_BRANCH, SOME_ACTOR, SOME_COMMIT_MESSAGE
        )

    branch = local_repo.create_head(SOME_FEATURE_BRANCH, force=True)
    branch.checkout()
    test_file_path.write_text("content two")
    stage_commit_push_changes(
        local_repo,
        SOME_FEATURE_BRANCH,
        SOME_ACTOR,
        SOME_COMMIT_MESSAGE,
        kwargs_to_push={"force": True},
    )


def test_feature_branch__untracked_files_present__raises_pygitops_error(mocker):
    untracked_file = "foo.py"
    repo = mocker.Mock(
        untracked_files=[untracked_file],
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    with pytest.raises(PyGitOpsError, match=untracked_file):
        with feature_branch(repo, SOME_FEATURE_BRANCH):
            pass


def test_feature_branch__active_branch_not_master__raises_pygitops_error(mocker):

    active_branch_name = "some_active_feature_branch"
    active_branch = mocker.Mock()
    repo = mocker.Mock(
        untracked_files=[],
        active_branch=mocker.Mock(),
        heads={active_branch_name: active_branch, GIT_BRANCH_MASTER: None},
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    with pytest.raises(PyGitOpsError):
        with feature_branch(repo, SOME_FEATURE_BRANCH):
            pass


def test_feature_branch__master_not_present_in_origin_refs__local_master_not_updated(
    mocker,
):

    origin_mock = mocker.Mock(refs=[])
    remotes_mock = mocker.Mock(origin=origin_mock)
    local_master_branch = mocker.Mock()

    repo = mocker.Mock(
        untracked_files=[],
        active_branch=local_master_branch,
        remotes=remotes_mock,
        working_dir=SOME_REPO_NAME,
        heads={GIT_BRANCH_MASTER: local_master_branch},
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    _checkout_pull_branch_mock = mocker.patch(
        "pygitops.operations._checkout_pull_branch"
    )

    with feature_branch(repo, SOME_FEATURE_BRANCH):
        pass

    _checkout_pull_branch_mock.assert_not_called()


def test_feature_branch__master_present_in_origin_refs__local_master_updated(mocker):

    origin_mock = mocker.Mock(refs=[GIT_BRANCH_MASTER])
    remotes_mock = mocker.Mock(origin=origin_mock)
    local_master_branch = mocker.Mock()

    repo = mocker.Mock(
        untracked_files=[],
        active_branch=local_master_branch,
        remotes=remotes_mock,
        working_dir=SOME_REPO_NAME,
        heads={GIT_BRANCH_MASTER: local_master_branch},
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )
    _checkout_pull_branch_mock = mocker.patch(
        "pygitops.operations._checkout_pull_branch"
    )

    with feature_branch(repo, SOME_FEATURE_BRANCH):
        pass

    _checkout_pull_branch_mock.assert_called_once_with(repo, GIT_BRANCH_MASTER)


@pytest.mark.parametrize(
    ["feature_branch_name", "checkout_expected"],
    ((SOME_FEATURE_BRANCH, True), (GIT_BRANCH_MASTER, False)),
)
def test_feature_branch__conditional_branch_checkout(
    mocker, feature_branch_name, checkout_expected
):

    origin_mock = mocker.Mock(refs=[GIT_BRANCH_MASTER])
    remotes_mock = mocker.Mock(origin=origin_mock)
    local_master_branch = mocker.Mock()
    feature_branch_mock = mocker.Mock()

    mocker.patch("pygitops.operations._checkout_pull_branch")
    repo = mocker.Mock(
        untracked_files=[],
        active_branch=local_master_branch,
        remotes=remotes_mock,
        working_dir=SOME_REPO_NAME,
        heads={GIT_BRANCH_MASTER: local_master_branch},
        create_head=mocker.Mock(return_value=feature_branch_mock),
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    with feature_branch(repo, feature_branch_name):
        pass

    assert feature_branch_mock.checkout.called == checkout_expected


def test_feature_branch__exception_within_context__cleanup_occurs(mocker):

    some_branch_name = "some-feature-branch"
    origin_mock = mocker.Mock(refs=[GIT_BRANCH_MASTER])
    remotes_mock = mocker.Mock(origin=origin_mock)
    local_master_branch = mocker.Mock()

    mocker.patch("pygitops.operations._checkout_pull_branch")

    repo_mock = mocker.Mock(
        untracked_files=[],
        active_branch=local_master_branch,
        remotes=remotes_mock,
        working_dir=SOME_REPO_NAME,
        heads={GIT_BRANCH_MASTER: local_master_branch},
        create_head=mocker.Mock(),
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    with pytest.raises(Exception):
        with feature_branch(repo_mock, some_branch_name):
            raise Exception("some exception")

    local_master_branch.checkout.assert_called_once()


def test_feature_branch__nested_calls__raises_pygitops_error(mocker):
    """Make sure the feature_branch context manager locks the repo correctly."""

    some_branch_name = "some-feature-branch"
    timeout_message = re.escape(
        f"The timeout of 10 seconds was exceeded when attempting to acquire the lockfile: lockfiles/{SOME_REPO_NAME}_lock_file.lock"
    )
    origin_mock = mocker.Mock(refs=[GIT_BRANCH_MASTER])
    remotes_mock = mocker.Mock(origin=origin_mock)
    local_master_branch = mocker.Mock()

    repo_mock = mocker.Mock(
        untracked_files=[],
        active_branch=local_master_branch,
        remotes=remotes_mock,
        working_dir=SOME_REPO_NAME,
        heads={GIT_BRANCH_MASTER: local_master_branch},
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )

    with feature_branch(repo_mock, some_branch_name):
        with pytest.raises(
            PyGitOpsError,
            match=timeout_message,
        ):
            with feature_branch(repo_mock, some_branch_name):
                pass


def test_get_updated_repo__git_error_raised_by_repo__raises_pygitops_error(mocker):
    """GitError is the base exception class for the GitPython API so any exceptions raised by it will be GitErrors"""

    mocker.patch("pygitops.operations.Repo.clone_from", side_effect=GitError)

    with pytest.raises(PyGitOpsError):
        get_updated_repo(SOME_CLONE_REPO_URL, SOME_CLONE_PATH)


def test_get_updated_repo__repo_dne__fresh_clone_performed(mocker, tmp_path):

    clone_from_mock = mocker.patch("pygitops.operations.Repo.clone_from")

    get_updated_repo(SOME_CLONE_REPO_URL, tmp_path)

    clone_from_mock.assert_called_once_with(SOME_CLONE_REPO_URL, tmp_path)


def test_get_updated_repo__repo_dne__kwargs_passed_to_clone_from(mocker, tmp_path):

    clone_from_mock = mocker.patch("pygitops.operations.Repo.clone_from")

    some_kwargs = {"some_arg": "some-value", "another_arg": "another-value"}

    get_updated_repo(SOME_CLONE_REPO_URL, tmp_path, **some_kwargs)

    clone_from_mock.assert_called_once_with(
        SOME_CLONE_REPO_URL, tmp_path, **some_kwargs
    )


def test_get_updated_repo__repo_exists_locally__repo_update_performed_against_default_branch(
    mocker, tmp_path
):

    Repo.init(tmp_path)
    master_branch_mock = mocker.Mock()
    repo_mock = mocker.Mock(
        heads={"master": master_branch_mock},
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value=SOME_HEAD_REF)),
    )
    mocker.patch("pygitops.operations.Repo", return_value=repo_mock)

    get_updated_repo(SOME_CLONE_REPO_URL, tmp_path)

    master_branch_mock.checkout.assert_called_once()
    repo_mock.remotes.origin.pull.assert_called_once()


def test_get_updated_repo__repo_exists_locally__repo_update_performed_against_provided_branch(
    mocker, tmp_path
):

    repo_mock = mocker.Mock()
    Repo.init(tmp_path)
    get_default_branch_mock = mocker.patch("pygitops.operations.get_default_branch")
    _checkout_pull_branch_mock = mocker.patch(
        "pygitops.operations._checkout_pull_branch"
    )
    mocker.patch("pygitops.operations.Repo", return_value=repo_mock)

    get_updated_repo(SOME_CLONE_REPO_URL, tmp_path, branch=SOME_FEATURE_BRANCH)

    get_default_branch_mock.assert_not_called()
    _checkout_pull_branch_mock.assert_called_once_with(repo_mock, SOME_FEATURE_BRANCH)


def test_get_updated_repo__clone_dirs_dne__clone_dirs_created(mocker, tmp_path):

    clone_dir = tmp_path / "some_parent" / "repo"
    repo_mock = mocker.Mock()
    mocker.patch("pygitops.operations.Repo", return_value=repo_mock)

    get_updated_repo(SOME_CLONE_REPO_URL, clone_dir)

    assert clone_dir.exists()


def test_get_updated_repo__file_operations__repo_not_present(tmp_path):
    """
    A fresh clone of a repository should pull down remote content

    Configures 'remote' repository with initial content
    Cloning the remote repo should create the expected content in the new local repository
    """

    # initialize remote repo
    remote_path = tmp_path / "remote"
    local_path = tmp_path / "local"
    local_path.mkdir()
    remote_repo = _initialize_repo_with_content(remote_path)

    # write and commit some content in the remote repo
    _commit_content(remote_repo, SOME_INITIAL_CONTENT)

    # clone remote repo to local
    local_repo = get_updated_repo(str(remote_path), local_path)

    filepath = f"{local_repo.working_tree_dir}/{SOME_CONTENT_FILENAME}"

    # content from remote should be present in local repo
    with open(filepath, "r") as test_file:
        content = test_file.read()
        assert SOME_INITIAL_CONTENT in content


def test_get_updated_repo__local_repo_on_disk__remote_default_branch_changes__remote_default_pulled(
    tmp_path,
):

    remote_path = tmp_path / "remote"
    local_path = tmp_path / "local"
    local_path.mkdir()
    remote_repo = _initialize_repo_with_content(remote_path)

    local_repo = get_updated_repo(str(remote_path), local_path)

    assert local_repo.active_branch.name != SOME_DEFAULT_BRANCH_NAME

    # create and update head ref on remote repo
    default_head = remote_repo.create_head(SOME_DEFAULT_BRANCH_NAME)
    remote_repo.head.set_reference(default_head)

    local_repo = get_updated_repo(str(remote_path), local_path)
    assert local_repo.active_branch.name == SOME_DEFAULT_BRANCH_NAME


def test_get_updated_repo__file_operations__repo_present_locally(tmp_path):
    """
    A clone of a repository that already exists locally should checkout master branch and pull down latest content

    Configures "remote" repository with initial content, and clones repo to local machine

    We will move the local repo to another branch, and make an additional commit on the master branch of the remote repo
    The side effect of running the clone operation is that the master branch is checked out and updated locally
    """

    # initialize remote repo
    remote_path = tmp_path / "remote"
    local_path = tmp_path / "local"
    local_path.mkdir()
    remote_repo = _initialize_repo_with_content(remote_path)

    # write and commit some content in the remote repo
    _commit_content(remote_repo, SOME_INITIAL_CONTENT)

    # setup the preconditions outlined in our test case description
    local_repo = get_updated_repo(str(remote_path), local_path)
    local_repo.create_head(SOME_FEATURE_BRANCH)
    local_repo.heads[SOME_FEATURE_BRANCH].checkout()
    _commit_content(remote_repo, SOME_NEW_CONTENT)

    # act, asserting expected state before and after operation
    with _assert_get_updated_repo_state(local_repo):
        get_updated_repo(str(remote_path), local_path)


def test_get_updated_repo__error__login_not_in_error(mocker):

    mocker.patch(
        "pygitops.operations.Repo.clone_from",
        side_effect=GitCommandError("some-command", "some-status"),
    )

    with pytest.raises(PyGitOpsError) as exc_info:
        get_updated_repo(SOME_CLONE_REPO_URL, SOME_CLONE_PATH)

    assert SOME_SERVICE_ACCOUNT_TOKEN not in str(exc_info.value)


def test_get_updated_repo__error__login_scrubbed(mocker):
    mocker.patch(
        "pygitops.operations.Repo.clone_from",
        side_effect=GitError(SOME_CLONE_REPO_URL),
    )

    with pytest.raises(PyGitOpsError) as exc_info:
        get_updated_repo(SOME_CLONE_REPO_URL, SOME_CLONE_PATH)

    exception_text = str(exc_info.value)
    assert "https://***:***@" in exception_text
    assert SOME_SERVICE_ACCOUNT_TOKEN not in exception_text


def test_get_updated_repo__clone_dir_as_str(mocker, tmp_path):

    clone_from_mock = mocker.patch(
        "pygitops.operations.Repo.clone_from",
    )

    mocker.patch("pygitops.operations._is_git_repo", mocker.Mock(return_value=False))
    get_updated_repo(SOME_CLONE_REPO_URL, str(tmp_path))

    assert clone_from_mock.called
    assert clone_from_mock.call_args[0][1] == PosixPath(str(tmp_path))


def test_get_default_branch__match_not_present__raises_pygitops_error(mocker):

    repo_mock = mocker.Mock(
        git=mocker.Mock(
            symbolic_ref=mocker.Mock(return_value="some-unmatched-symbolic-ref")
        )
    )

    with pytest.raises(PyGitOpsError):
        get_default_branch(repo_mock)


def test_get_default_branch__match_index_error__raises_pygitops_error(mocker):

    repo_mock = mocker.Mock(
        git=mocker.Mock(symbolic_ref=mocker.Mock(return_value="refs/remotes/origin/"))
    )

    mocker.patch(
        "pygitops.operations.re",
        new=mocker.Mock(
            match=mocker.Mock(
                return_value=mocker.Mock(group=mocker.Mock(side_effect=IndexError))
            )
        ),
    )

    with pytest.raises(PyGitOpsError):
        get_default_branch(repo_mock)


def test_get_default_branch__default_branch_returned(tmp_path):

    repos = _initialize_multiple_empty_repos(tmp_path)
    remote_repo = repos.remote_repo
    local_repo = repos.local_repo

    # the local repo's default branch should reflect the HEAD ref on the remote branch
    assert get_default_branch(local_repo) == remote_repo.heads[0].name


def test_get_default_branch__remote_head_changes__new_default_branch_returned(tmp_path):

    repos = _initialize_multiple_empty_repos(tmp_path)
    remote_repo = repos.remote_repo
    local_repo = repos.local_repo

    # initially, the local repo's default branch should reflect the HEAD ref on the remote branch
    assert get_default_branch(local_repo) == remote_repo.heads[0].name

    # point remote repo's HEAD ref at new branch
    new_branch = remote_repo.create_head(GIT_BRANCH_MAIN)
    remote_repo.head.reference = new_branch

    assert get_default_branch(local_repo) == GIT_BRANCH_MAIN


def _initialize_repo_with_content(repo_path):
    """
    Helper function used to initialize repo objects, write content, and make initial commit
    """

    repo_path.mkdir()
    repo = Repo.init(repo_path)

    _commit_content(repo, SOME_INITIAL_CONTENT, commit_message="Initial commit")

    return repo


def _commit_content(repo, content, commit_message="another commit"):
    """
    Helper function used to commit content to repository
    """
    with open(f"{repo.working_tree_dir}/{SOME_CONTENT_FILENAME}", "a+") as test_file:
        test_file.write(content)
    index = repo.index
    index.add([SOME_CONTENT_FILENAME])
    index.commit(commit_message)


@contextmanager
def _assert_get_updated_repo_state(repo):
    """
    Runs assertions before and after clone operation, in case where repo already exists locally
    """

    filepath = f"{repo.working_tree_dir}/{SOME_CONTENT_FILENAME}"

    # prior to running the clone operation, `SOME_FEATURE_BRANCH` is the active feature branch
    assert repo.active_branch == repo.heads[SOME_FEATURE_BRANCH]
    with open(filepath, "r") as test_file:
        content = test_file.read()
        assert SOME_INITIAL_CONTENT in content
        assert SOME_NEW_CONTENT not in content

    yield

    # after running the clone operation, `GIT_BRANCH_MASTER` is the active feature branch, and the new content is present
    assert repo.active_branch == repo.heads[GIT_BRANCH_MASTER]
    with open(filepath, "r") as test_file:
        content = test_file.read()
        assert SOME_INITIAL_CONTENT in content
        assert SOME_NEW_CONTENT in content


@contextmanager
def _assert_branch_state_stage_commit_push_changes__file_added(remote_repo, local_repo):
    """Run assertions before and after staging, committing, and pushing for a given repo pair."""

    local_content_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME

    # The file should exist only on local before pushing
    assert SOME_INITIAL_CONTENT in local_content_path.read_text()

    yield

    # The remote repo should now have at least one commit,
    # and the commit history should be present on both local and remote after pushing

    assert len(list(remote_repo.iter_commits())) != 0
    assert list(remote_repo.iter_commits()) == list(local_repo.iter_commits())


@contextmanager
def _assert_branch_state_stage_commit_push_changes__file_removed(
    remote_repo, local_repo
):
    """Run assertions before and after staging, committing, and pushing for a given repo pair."""
    local_content_path = Path(local_repo.working_dir) / SOME_CONTENT_FILENAME

    # The file should exist only on local before pushing
    assert SOME_INITIAL_CONTENT in local_content_path.read_text()

    yield

    # The file should now be removed on local
    assert not local_content_path.exists()
    # The commit history should be the same on both local and remote after pushing
    # (including the commit to remove the file)
    assert list(remote_repo.iter_commits()) == list(local_repo.iter_commits())


# Helper functions for testing git operations
def _initialize_multiple_empty_repos(base_path) -> MultipleTestingRepos:
    """
    Helper function used to initialize and configure local, remote, and clone repos for integration testing.
    """

    # Setup Test Case
    local_path = base_path / "local"
    local_path.mkdir()

    remote_path = base_path / "remote.git"
    remote_path.mkdir()

    # We have to set up a clone because we can't commit directly to a bare repo
    clone_path = base_path / "clone"
    clone_path.mkdir()

    # The remote is set up as a bare repository
    remote_repo = Repo.init(remote_path)

    # give the remote repo some initial commit history
    new_file_path = remote_path / SOME_CONTENT_FILENAME
    new_file_path.write_text(SOME_CHANGES)
    remote_repo.index.add([str(new_file_path)])
    remote_repo.index.commit(
        SOME_COMMIT_MESSAGE, author=SOME_ACTOR, committer=SOME_ACTOR
    )

    # Simplify things by assuring local copies are cloned from the remote.
    # Because they are clones, they will have 'origin' correctly configured
    local_repo = Repo.clone_from(remote_repo.working_dir, local_path)
    cloned_repo = Repo.clone_from(remote_repo.working_dir, clone_path)

    return MultipleTestingRepos(
        remote_repo=remote_repo, local_repo=local_repo, cloned_repo=cloned_repo
    )


def _get_diff(repo: Repo) -> str:
    """
    Helper function used to handle the logic of generating diff text via a feature branch.

    This diff will only reflect the changes since the last commit.
    This includes staging the local changes.
    """

    index = repo.index
    workdir_path = Path(repo.working_dir)

    untracked_file_paths = [Path(f) for f in repo.untracked_files]
    items_to_stage = untracked_file_paths + [Path(f.a_path) for f in index.diff(None)]

    for item in items_to_stage:
        full_path = workdir_path / item
        index.add(str(item)) if full_path.exists() else index.remove(str(item), r=True)

    return repo.git.diff("--cached")
