# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Added optional `force` arg to `checkout_pull_branch`, allowing any uncommitted changes in an existing repository to be discarded. (#246)

## [0.15.0] - 2022-05-24

### Changed

* Calls to `Path.mkdir` are now made with the `exist_ok=True` parameter, eliminating a race condition when multiple workers are   attempting to create the same directory.

* Bump bandit from 1.7.1 to 1.7.2
* Bump mkdocs-material from 8.1.2 to 8.1.8
* Bump actions/checkout from 2 to 3
* Bump actions/setup-python from 2 to 3.1.1
* Bump actions/upload-artifact from 2 to 3
* Bump mypy from 0.931 to 0.950


## [0.14.0] - 2022-04-26

### Added

* Add kwarg pass-through parameter to `stage_commit_push_changes`, allowing users to provide keyword arguments to `git push`.

### Changed

* Bumped mkdocstrings from 0.17.0 to 0.18.1
* Bump black from 22.1.0 to 22.3.0

### Removed

* Support for Python 3.6


## [0.13.2] - 2022-03-10

### Changed

- Loosened the Gitpython version requirement range

## [0.13.1] - 2022-01-06

### Added

- Python version `3.10` tested during CI
- Python version `3.10` added to package classifiers

### Changed

- Improved debug-level logging `stage_commit_push_changes` function

## [0.13.0] - 2021-09-22

### Changed

* Change in behavior for `pygitops.operations.stage_commit_push_changes`:
  * Previously, the `items_to_stage` optional argument will drive autodiscovery of items to stage if not provided.
  * Previously, when no items to stage are discovered, a `PyGitOpsError` is raised.
  * The new change in behavior allows `items_to_stage` to be explicitly set to `[]`, indicating that the caller does not want autodiscovery of items to stage to occur, and the list is indeed empty.
  * This change caters to more advanced use cases such as [performing automated updates to git submodules where staged changes are intentionally absent](https://wayfair-incubator.github.io/pygitops/making-changes-on-feature-branch/#advanced-example)

## [0.12.1] - 2021-09-21

### Changed

* Restrict the allowable version range of GitPython to >=3.1,<=3.1.18
  * Newer versions of GitPython have had significant issues with typehinting that are proving to be incompatible with mypy

## [0.12.0] - 2021-08-30

### Changed

* Cleaned up the working directory on feature branch when we exit feature branch context manager.

## [0.11.1] - 2021-05-17

### Fixed

* Properly increment version number to `0.11.1` (version `0.11.0` was not tagged properly so it was not pushed to PyPI)

## [0.11.0] - 2021-05-14

### Changed

* Removed `repo_name` parameter of the `get_updated_repo` function to give the user control of exactly where to clone the repo contents to. The `clone_dir` argument is now the directory into which the contents of the repo will be cloned.

## [0.10.0] - 2021-05-07

### Added

- First public release!!!

[Unreleased]: https://github.com/wayfair-incubator/pygitops/compare/v0.15.0...main
[0.15.0]: https://github.com/wayfair-incubator/pygitops/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/wayfair-incubator/pygitops/compare/v0.13.2...v0.14.0
[0.13.2]: https://github.com/wayfair-incubator/pygitops/compare/v0.13.1...v0.13.2
[0.13.1]: https://github.com/wayfair-incubator/pygitops/compare/v0.13.0...v0.13.1
[0.13.0]: https://github.com/wayfair-incubator/pygitops/compare/v0.12.1...v0.13.0
[0.12.1]: https://github.com/wayfair-incubator/pygitops/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/wayfair-incubator/pygitops/compare/v0.11.1...v0.12.0
[0.11.1]: https://github.com/wayfair-incubator/pygitops/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/wayfair-incubator/pygitops/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/wayfair-incubator/pygitops/compare/af37d9a...v0.10.0
