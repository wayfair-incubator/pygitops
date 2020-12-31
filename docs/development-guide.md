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

## Publishing the Package

TODO: Document package publish process

## Continuous Integration Pipeline

TODO: Add CI documentation.

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
