import pytest

from pygitops._constants import GITHUB_PUBLIC_DOMAIN_NAME
from pygitops.remote_git_utils import _scrub_github_auth, build_github_repo_url
from tests.test_operations import (
    SOME_GITHUB_DOMAIN_NAME,
    SOME_REPO_NAME,
    SOME_REPO_NAMESPACE,
    SOME_SERVICE_ACCOUNT_NAME,
    SOME_SERVICE_ACCOUNT_TOKEN,
)


def test_build_github_repo_url__expected_repo_url_returned():
    assert (
        build_github_repo_url(
            SOME_SERVICE_ACCOUNT_NAME,
            SOME_SERVICE_ACCOUNT_TOKEN,
            SOME_REPO_NAMESPACE,
            SOME_REPO_NAME,
            SOME_GITHUB_DOMAIN_NAME,
        )
        == f"https://{SOME_SERVICE_ACCOUNT_NAME}:{SOME_SERVICE_ACCOUNT_TOKEN}@{SOME_GITHUB_DOMAIN_NAME}/{SOME_REPO_NAMESPACE}/{SOME_REPO_NAME}.git"
    )


def test_build_github_repo_url__github_domain_name_not_provided__public_github_url_built():
    assert (
        build_github_repo_url(
            SOME_SERVICE_ACCOUNT_NAME,
            SOME_SERVICE_ACCOUNT_TOKEN,
            SOME_REPO_NAMESPACE,
            SOME_REPO_NAME,
        )
        == f"https://{SOME_SERVICE_ACCOUNT_NAME}:{SOME_SERVICE_ACCOUNT_TOKEN}@{GITHUB_PUBLIC_DOMAIN_NAME}/{SOME_REPO_NAMESPACE}/{SOME_REPO_NAME}.git"
    )


@pytest.mark.parametrize(
    ("input_", "output"),
    [
        (
            "https://some-service-account-name:test_cred_123@some-github-domain-name/test_namespace/some-repo-name.git",
            "https://***:***@some-github-domain-name/test_namespace/some-repo-name.git",
        )
    ],
)
def test__scrub_github_auth_1(input_, output):
    """
    Validate Github auth tokens are scrubbed from URLs
    """
    assert _scrub_github_auth(input_) == output
