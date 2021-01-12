from git import Repo


# Placeholder function to test autogeneration of function documentation.
# Will remove during https://github.com/wayfair-incubator/pygitops/issues/23
def get_updated_repo(repo_name: str) -> Repo:
    """
    Get the specified repository, updating if already present.

    :param repo_name: Name of the repository.
    """
    return Repo.init("some-path")
