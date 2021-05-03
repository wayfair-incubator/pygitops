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

# create a Repo object in the current directory (see https://gitpython.readthedocs.io/en/stable/tutorial.html#meet-the-repo-type)
REPO = Repo(self.rorepo.working_tree_dir)

with feature_branch(REPO, NEW_BRANCH_NAME):
    # create a new file with a list of chores
    Path(NEW_FILE_NAME).write_text('- [ ] haircut\n- [ ] groceries\n- [ ] dishes')

    # stage, commit, and push these changes
    stage_commit_push_changes(REPO, NEW_BRANCH_NAME, ACTOR, COMMIT_MESSAGE)
```

Focusing on the portion of the code starting at the line with `with feature_branch(REPO, NEW_BRANCH_NAME):`,
we can generalize the workflow as:

- Create a new, feature branch
- Make changes
- Stage, commit, and push changes
- Return to the default branch

This is a common pattern when automating git workflows; using `feature_branch` and `stage_commit_push_changes` makes it easy to capture this flow in Python.
