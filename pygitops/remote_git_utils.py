"""Utilities for working with git remotes."""

import re

from pygitops._constants import GITHUB_PUBLIC_DOMAIN_NAME


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


def _scrub_github_auth(string: str) -> str:
    sa_token_regex = "https://.+?:.+?@"  # nosec
    sa_token_replace_term = "https://***:***@"  # nosec

    return re.sub(sa_token_regex, sa_token_replace_term, string)
