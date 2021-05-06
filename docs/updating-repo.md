# Pulling Updated Repo

pygitops make it easy to clone and/or update a repo. In this guide, we'll see how by looking at the `get_updated_repo` function.

## Background

Let's say we want to automate some changes to a repository. First, we need to clone the repo locally. When doing this, however, we must keep in mind that we may already have the repo cloned locally, so we would want to check to see if the repo exists before cloning it. If it does not exist, we want to clone it. If it does exist, we want to pull updates on the given branch. In summary a common, useful workflow is this:

1. Check to see if a given repo exists
1. If repo exists:
    - Pull updates
1. If repo does not exist:
    - Clone it

This workflow is encapsulated in the `get_updated_repo` function.

As documented, this function will "Clone the default branch of the target repository, returning a repo object. If repo is already present, we will pull in the latest changes to the default branch of the repo."

## Example

Below is an example which clones the [Columbo repository][columbo-repo] into the `columbo` directory within the `~/repos` directory.

```python
from pygitops.operations import get_updated_repo

repo = get_updated_repo('https://github.com/wayfair-incubator/columbo.git', '~/repos', 'columbo')
```

Again, the value of this function is that you don't have to know if the Columbo repo has already been cloned. If you run `repo = get_updated_repo('https://github.com/wayfair-incubator/columbo.git', '~/repos', 'columbo')` again, it will not clone the repo again, but will only pull updates from the default branch.

[columbo-repo]: https://github.com/wayfair-incubator/columbo
