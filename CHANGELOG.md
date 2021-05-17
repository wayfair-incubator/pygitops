# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.1] - 2021-05-17

### Fixed

* Properly increment version number to `0.11.1` (version `0.11.0` was not tagged properly so it was not pushed to PyPI)

## [0.11.0] - 2021-05-14

### Changed

* Removed `repo_name` parameter of the `get_updated_repo` function to give the user control of exactly where to clone the repo contents to. The `clone_dir` argument is now the directory into which the contents of the repo will be cloned.

## [0.10.0] - 2021-05-07

### Added

- First public release!!!
