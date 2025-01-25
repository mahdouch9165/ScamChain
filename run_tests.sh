#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# OPTIONAL: Activate your virtual environment
# source venv/bin/activate

echo "Running pytest with forked mode..."
pytest -n auto src/tests

echo "All tests completed!"
