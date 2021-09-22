# Making Changes on a Feature Branch

pygitops make it easy to make changes on a new, feature branch of a repo. In this guide, we'll see how by looking at the `feature_branch` context manager
and the `stage_commit_push_changes` function.

## Example

Here is an example using the `feature_branch` context manager and the `stage_commit_push_changes` function:

```python
from pathlib import Path

from pygitops.operations import feature_branch, stage_commit_push_changes
from git import Actor, Repo

NEW_FILE_NAME = 'chores.txt'
NEW_BRANCH_NAME = 'adding-chores'
ACTOR = Actor('git-username', 'git-email@example.com')
COMMIT_MESSAGE = 'Adding chores'
SOME_DIRECTORY = 'some-directory'

# create a Repo object in the current directory (see https://gitpython.readthedocs.io/en/stable/tutorial.html#meet-the-repo-type)
repo = Repo(SOME_DIRECTORY)

with feature_branch(REPO, NEW_BRANCH_NAME):
    # create a new file with a list of chores
    (Path(SOME_DIRECTORY) / NEW_FILE_NAME).write_text('- [ ] haircut\n- [ ] groceries\n- [ ] dishes')

    # stage, commit, and push these changes
    stage_commit_push_changes(repo, NEW_BRANCH_NAME, ACTOR, COMMIT_MESSAGE)
```

Focusing on the portion of the code starting at the line with `with feature_branch(repo, NEW_BRANCH_NAME):`,
we can generalize the workflow as:

- Create a new, feature branch
- Make changes
- Stage, commit, and push changes
- Return to the default branch

This is a common pattern when automating git workflows; using `feature_branch` and `stage_commit_push_changes` makes it easy to capture this flow in Python.

## Advanced Example

In the below example, we have a repository that contains [git submodules][git_submodules].

The submodule references a git repository rather than containing its code.

In some cases, you may want to automate updates to this reference.

The below example demonstrates several key concepts:

- Using `repo.git`, we are able to directly execute git commands such as `submodule update --remote` and `add SOME_SUBMODULE_REPO_NAME`
- When we execute `stage_commit_push_changes`, we would like to commit to a feature branch, but no items are available to be staged.
  - Here, we explicitly provide the `items_to_stage=[]` to indicate that we intentionally have no items to stage.
  - Otherwise, the operation will infer staged items for us, and raise a `PyGitOpsError` when no staged items are discovered.

```python
from pygitops.operations import feature_branch, stage_commit_push_changes
from git import Actor, Repo

NEW_BRANCH_NAME = 'some-new-branch'
ACTOR = Actor('git-username', 'git-email@example.com')
REPO = Repo(SOME_DIRECTORY)
COMMIT_MESSAGE = 'automated submodule update
SOME_SUBMODULE_REPO_NAME = 'some-repo'

# update submodule's reference to remote upstream, push feature branch with changes
with feature_branch(repo, NEW_BRANCH_NAME):

    # update the submodules's reference to the remote repo
    repo.git.submodule("update", "--remote")

    # stage changes ourselves so that we can use the porcelain `git add <file>` command
    # tell `stage_commit_push_changes()` to not stage anything itself via `items_to_stage=[]`
    repo.git.add(SOME_SUBMODULE_REPO_NAME)

    stage_commit_push_changes(
        repo,
        NEW_BRANCH_NAME,
        ACTOR,
        COMMIT_MESSAGE,
        items_to_stage=[],
    )
```

[git_submodules]: https://git-scm.com/book/en/v2/Git-Tools-Submodules
