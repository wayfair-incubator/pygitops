# Development Guide

Welcome - Thank you for wanting to make this project better! This section provides an overview on how the repository is structured
and how to work with the codebase.

Before you dive into this guide, please read the following first:

* The [Code of Conduct][code of conduct]
* The [Contributing Guide][contributing]

## Docker

The pygitops project uses Docker to ease setting up a consistent development environment. The Docker documentation has
details on how to [install Docker][install-docker] and [install Docker Compose][install-docker-compose] on your computer.

Once you have installed Docker and Docker Compose, you can execute the test suite by running the following command from your terminal:

```bash
docker-compose run --rm test
```

If you want to be able to execute code in the container:

```bash
docker-compose run --rm devbox
(your code here)
```

In the devbox environment you'll be able to enter a Python shell and import `pygitops` or any dependencies.
The devbox environment also comes with `git-core` - a system dependency needed to run `gitpython`, our package's main dependency.

## Debugging

The Docker container has [pdb++][pdbpp-home] installed that can be used as a debugger. (However, you are welcome to set up
a different debugger if you would like.)

This allows you to easily create a breakpoint anywhere in the code.

```python
def my_function():
    breakpoint()
    ...
```

When you run your code, you will drop into an interactive `pdb++` debugger.

See the documentation on [pdb][pdb-docs] and [pdb++][pdbpp-docs] for more information.

## Testing

You'll be unable to merge code unless the linting and tests pass. You can run these in your container via:

```bash
docker-compose run --rm test
```

This will run the same tests, linting, and code coverage that are run by the CI pipeline. The only difference is that when run locally, `black` and `isort` are configured to automatically correct issues they detect.

Generally we should endeavor to write tests for every feature. Every new feature branch should increase the test
coverage rather than decrease it.

We use [pytest][pytest-docs] as our testing framework.

#### Stages

To customize / override a specific testing stage, please read the documentation specific to that tool:

1. [PyTest][pytest-docs]
2. [MyPy][mypy-docs]
3. [Black][black-docs]
4. [Isort][isort-docs]
5. [Flake8][flake8-docs]
6. [Bandit][bandit-docs]

### `setup.py`

Setuptools is used to package the library.

**`setup.py` must not import anything from the package** When installing from source, the user may not have the
packages' dependencies installed, and importing the package is likely to raise an `ImportError`. For this reason, the
**package version should be obtained without importing**. This explains why `setup.py` uses a regular expression to
grab the version from `__init__.py` without actually importing any dependencies.

### Requirements

* **requirements.txt** - Lists all direct dependencies (packages imported by the library).
* **Requirements-test.txt** - Lists all direct requirements needed to run the test suite & lints.

## Publishing a New Version

Once the package is ready to be released, there are a few things that need to be done:

1. Run the version bump script with the appropriate part name (`major`, `minor`, or `patch`).
    Example: `docker-compose run --rm bump minor`
    
    This will update all affected files (including changelog) with the new version on whichever branch you are on

2. Create a pull request from your branch.
3. Get the pull request approved.
4. Merge the pull request to the default branch.

!!! warning
    Take care not to run bump script more than once!

Merging the pull request will trigger a GitHub Action that will create a new release. The creation of this new
release will trigger a GitHub Action that will trigger a wheel build & a source distributions of the package and push them to
[PyPI][pypi].

!!! warning
    The action that uploads the files to PyPI will not run until a repository maintainer acknowledges that the job is
    ready to run. This is to keep the PyPI publishing token secure. Otherwise, any job would have access to the token. 

In addition to uploading the files to PyPI, the documentation website will be updated to include the new version. If the
new version is a full release, it will be made the new `latest` version.

## Continuous Integration Pipeline

The Continuous Integration (CI) Pipeline runs to confirm that the repository is in a good state. It will run when 
someone creates a pull request or when they push new commits to the branch for an existing pull request. The pipeline
runs multiple different jobs that helps verify the state of the code.

This same pipeline also runs on the default branch when a maintainer merges a pull request.

### Lints

The first set of jobs that run as part of the CI pipline are linters that perform static analysis on the code. This
includes: [MyPy][mypy-docs], [Black][black-docs], [Isort][isort-docs], [Flake8][flake8-docs], and [Bandit][bandit-docs].

### Tests

The next set of jobs run the unit tests using [PyTest][pytest-docs]. The pipeline runs the tests cases across each
supported version of Python to ensure compatibility.

For each run of the test cases, the job will record the test results and code coverage information. The pipeline uploads
the code coverage information to [CodeCov][codecov] to ensure that a pull request doesn't significantly reduce the total
code coverage percentage or introduce a large amount of code that is untested.

### Distribution Verification

The next set of jobs build the wheel distribution, installs in into a virtual environment, and then runs Python to
import the library version. This works as a smoke test to ensure that the library can be packaged correctly and used.
The pipeline runs the tests cases across each supported version of Python to ensure compatibility.

### Documentation

The remaining jobs are all related to documentation.

* A job runs each of the code examples that are used in the documentation to verify they produce the expected results.
* A job builds the documentation in strict mode so that it will fail if there are any errors. The job records the
    generated files so that the documentation website can be viewed in its rendered form.
* When the pipeline is running as a result of a maintainer merging a pull request to the default branch, a job runs that
    publishes the current state of the documentation to as the `dev` version. This will allow users to view the state of
    the documentation as it has changed since a maintainer published the `latest` version.

[usage-guide]: usage-guide/fundamentals.md
[code of conduct]: https://github.com/wayfair-incubator/pygitops/blob/main/CODE_OF_CONDUCT.md
[contributing]: https://github.com/wayfair-incubator/pygitops/blob/main/CONTRIBUTING.md
[install-docker]: https://docs.docker.com/install/
[install-docker-compose]: https://docs.docker.com/compose/install/
[pdbpp-home]: https://github.com/pdbpp/pdbpp
[pdb-docs]: https://docs.python.org/3/library/pdb.html
[pdbpp-docs]: https://github.com/pdbpp/pdbpp#usage
[pytest-docs]: https://docs.pytest.org/en/latest/
[mypy-docs]: https://mypy.readthedocs.io/en/stable/
[black-docs]: https://black.readthedocs.io/en/stable/
[isort-docs]: https://pycqa.github.io/isort/
[flake8-docs]: http://flake8.pycqa.org/en/stable/
[bandit-docs]: https://bandit.readthedocs.io/en/stable/
[pypi]: https://pypi.org/project/pygitops/
[codecov]: https://about.codecov.io/
