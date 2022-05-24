# pygitops - 0.15.0

[![CI pipeline status](https://github.com/wayfair-incubator/pygitops/workflows/CI/badge.svg?branch=main)][ci]

`pygitops` provides a convenience layer for developers wishing to automate git workflows with python.

Best of all, it works extremely well with [GitPython][gitpython] as well as [PyGithub][pygithub]!

`pygitops`' feature set improves the experience of:

* cloning git repositories
* keeping local repositories up to date with their remotes
* making code changes on a repository feature branch
* staging, commiting, and pushing changes to remote

## Examples

### Cloning Repo

Most automated git workflows involve interacting with a local clone of a repo. You might want to begin by having a copy of that repository on your local disk. `pygitops` will clone the repository for you, updating it when already present.

```python
from pygitops.remote_git_utils import build_github_repo_url
from pygitops.operations import get_updated_repo

service_account_name = 'some-service-account-name'
service_account_token = 'some-service-account-token'
repo_owner = 'wayfair-incubator'
repo_name = 'pygitops'

repo_url = build_github_repo_url(service_account_name, service_account_token, repo_owner, repo_name)

repo = get_updated_repo(repo_url, f'/repos/{repo_name}')
```

### Using GitPython

The `repo` returned by `get_updated_repo` is an instance of `git.Repo`, from the [GitPython][gitpython] package. If you are already familiar with the package and need to leverage its functionality, `pygitops` won't get in your way!

```python
>>> from git import Repo
>>> repo = Repo('some-repo')
>>> repo.working_dir
'User/repos/some-repo'
```

### Commiting Change

A common git automation use case is to commit some changes; pushing them to a remote feature branch. Here, we create a new file `chores.txt` and commit / push that change to the `new-chores` feature branch. You may then want to use [PyGithub][pygithub] to create a pull request from these changes.

```python
from pathlib import Path

from pygitops.operations import feature_branch, stage_commit_push_changes
from git import Actor

repo_name = 'some-repo'
branch_name = 'new-chores'
some_actor = Actor('some-service-account', 'some-service-account@some-enterprise.com')
commit_message = 'Add list of chores'

with feature_branch(repo, branch_name):
    Path('some-clone-dir' / repo_name / 'chores.txt').write_text('haircut\ngroceries\ndishes')

    stage_commit_push_changes(repo, branch_name, some_actor, commit_message)
```

## Where to Start?

TODO

## Detailed Documentation

TODO

## API Reference

TODO

[ci]: https://github.com/wayfair-incubator/pygitops/actions
[gitpython]: https://github.com/gitpython-developers/GitPython
[pygithub]: https://github.com/PyGithub/PyGithub
