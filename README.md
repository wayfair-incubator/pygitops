# pygitops

[![CI pipeline status](https://github.com/wayfair-incubator/pygitops/workflows/CI/badge.svg?branch=main)][ci]
[![PyPI](https://img.shields.io/pypi/v/pygitops)][pypi]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pygitops)][pypi]
[![codecov](https://codecov.io/gh/wayfair-incubator/pygitops/branch/main/graph/badge.svg)][codecov]
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)][mypy-home]
[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)][black-home]

Pygitops is a wrapper around low-level GitPython logic, that makes it very simple to do basic git operations. This system is especially useful for systems that create automated pull requests, or otherwise operate on contents of repositories locally. 

For example, clone a repository, make some changes, and push those changes to a branch:

```python
from pathlib import Path

from pygitops.operations import feature_branch, stage_commit_push_changes, get_updated_repo, build_github_repo_url
from git import Actor, Repo

repo_name = 'some-repo'
repo_namespace = 'some-namespace'
branch_name = 'new-chores'
some_actor = Actor('some-service-account', 'some-service-account@some-enterprise.com')
commit_message = 'Add list of chores'

# Build the URL for cloning the repository 
repo_url = build_github_repo_url(
    "some-service-account_name",
    "some-access-token",
    repo_namespace,
    repo_name,
    "github.com",
)

# Clone the repository to the local filesystem (updating the repo if it is already present)
repo: Repo = get_updated_repo(
    repo_url, Path("some-clone-dir" / repo_name) 
)

# Make some changes on a feature branch, commit and push the changes
with feature_branch(repo, branch_name):
    Path('some-clone-dir' / repo_name / 'chores.txt').write_text('haircut\ngroceries\ndishes')

    stage_commit_push_changes(repo, branch_name, some_actor, commit_message)
```

### Features

* Clone repositories to your local filesystem from any remote git repository
* Create feature branches and add commits, without worrying about the underlying GitPython complexity

### Installation

```
pip install pygitops
```

### Usage

For more information, please see the [pygitops docs][pygitops-docs]

[ci]: https://github.com/wayfair-incubator/pygitops/actions
[pypi]: https://pypi.org/project/pygitops/
[codecov]: https://codecov.io/gh/wayfair-incubator/pygitops
[mypy-home]: http://mypy-lang.org/
[black-home]: https://github.com/psf/black
[pygitops-docs]: https://wayfair-incubator.github.io/pygitops/
