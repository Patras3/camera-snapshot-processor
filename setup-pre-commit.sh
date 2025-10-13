#!/bin/bash
# Setup script for pre-commit hooks

set -e

echo "=========================================="
echo "Setting up pre-commit hooks"
echo "=========================================="
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q homeassistant aiohttp voluptuous pillow numpy

# Install pre-commit
echo "Installing pre-commit..."
pip install -q pre-commit

# Install git hooks
echo "Installing git hooks..."
pre-commit install

# Run tests once to verify
echo
echo "=========================================="
echo "Running initial tests..."
echo "=========================================="
echo

echo "Test 1: Integration tests"
python test_integration.py

echo
echo "Test 2: API flow tests"
python test_api_flow.py

echo
echo "Test 3: Frontend validation"
python test_frontend.py

echo
echo "=========================================="
echo "✅ Pre-commit setup complete!"
echo "=========================================="
echo
echo "Hooks installed:"
echo "  - Black (code formatting)"
echo "  - isort (import sorting)"
echo "  - flake8 (linting)"
echo "  - Integration tests"
echo "  - API flow tests"
echo "  - Frontend validation"
echo "  - File checks"
echo
echo "These will run automatically on every commit."
echo
echo "To run manually:"
echo "  pre-commit run --all-files"
echo
echo "To skip hooks (not recommended):"
echo "  git commit --no-verify"
echo
