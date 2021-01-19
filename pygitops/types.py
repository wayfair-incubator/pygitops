from pathlib import Path
from typing import Union


class GitDefaultBranch:
    """
    A sentinal / placeholder class used to represent the intention to use the default branch on a repository
    """


GitBranchType = Union[GitDefaultBranch, str]
PathOrStr = Union[Path, str]

GIT_DEFAULT_BRANCH = GitDefaultBranch()
