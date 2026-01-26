#!/usr/bin/env bash

set -eo pipefail

RUFF_FIX=""

function usage
{
    echo "usage: run_tests.sh [--format-code]"
    echo ""
    echo " --format-code : Format the code instead of checking formatting."
    exit 1
}

while [[ $# -gt 0 ]]; do
    arg="$1"
    case $arg in
        --format-code)
        RUFF_FIX="--fix"
        ;;
        -h|--help)
        usage
        ;;
        "")
        # ignore
        ;;
        *)
        echo "Unexpected argument: ${arg}"
        usage
        ;;
    esac
    shift
done

# only generate html locally
pytest tests --cov-report html

echo "Running ruff..."
if [ -z "${RUFF_FIX}" ]; then
    # ruff check: linter - finds code quality issues (unused imports, bugs, security issues)
    ruff check pygitops tests
    # ruff format: formatter - ensures consistent code style (indentation, quotes, line length)
    ruff format --check pygitops tests
else
    # ruff check --fix: auto-fix linting issues where possible
    ruff check --fix pygitops tests
    # ruff format: auto-format code style
    ruff format pygitops tests
fi

echo "Running mypy..."
mypy pygitops
