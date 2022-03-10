#!/usr/bin/env bash

# Referenced From: https://github.com/wayfair-incubator/columbo/blob/main/docker/bump_version.sh

set -eo pipefail

function usage() {
  echo "usage: bump_version.sh major|minor|patch"
  echo ""
  echo " major|minor|patch : Part of version string to updated."
  exit 1
}

if [[ $# != 1 || ! "${1}" =~ major|minor|patch ]]; then
  usage
else
  PART="${1}"
fi


# Capture value of new version
NEW_VERSION=$(bump2version --dry-run --allow-dirty --list "${PART}" | grep new_version | sed -r s,"^.*=",,)

# Update files
bump2version "${PART}" --allow-dirty

# Updating the changelog has to be done manually
#   - bump2version doesn't support inserting dates https://github.com/c4urself/bump2version/issues/133
#   - It is not possible to have a multiline string in an INI file where a line after the first line starts with '#'.
#     The config parser reads it as a comment line.
TODAY=$(date +%Y-%m-%d)
sed -i "s/## \[Unreleased\]/## \[Unreleased\]\n\n## \[${NEW_VERSION}\] - ${TODAY}/g" CHANGELOG.md


# Show effected files
git show --pretty="" --name-only
