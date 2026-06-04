#!/usr/bin/env bash
# setup.sh - Create and activate the virtual environment, install dependencies.
#
# Usage:
#   source setup.sh
#
# Must be run with `source` (not `bash setup.sh`) so that the venv activation
# persists in your current shell session.

set -e

# -----------------------------------------------------------------------
# Guard: must be sourced, not executed directly
# -----------------------------------------------------------------------
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: this script must be sourced, not executed directly."
    echo "Run: source setup.sh"
    exit 1
fi

# -----------------------------------------------------------------------
# Resolve project root (directory containing this script)
# -----------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

echo "=== last-known-position — Environment Setup ==="
echo "Project root: $SCRIPT_DIR"
echo ""

# -----------------------------------------------------------------------
# Create venv if it doesn't already exist
# -----------------------------------------------------------------------
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists, skipping creation."
else
    echo "→ Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created at .venv/"
fi

# -----------------------------------------------------------------------
# Activate
# -----------------------------------------------------------------------
echo "→ Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✓ Activated."

# -----------------------------------------------------------------------
# Install / sync dependencies
# -----------------------------------------------------------------------
if [ -f "$REQUIREMENTS" ]; then
    echo "→ Installing dependencies from requirements.txt..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "$REQUIREMENTS"
    echo "✓ Dependencies installed."
else
    echo "⚠ No requirements.txt found, skipping dependency install."
fi

# -----------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------
echo ""
echo "=== Setup complete. Your shell is now inside the virtual environment. ==="
echo "To run tests:      pytest"
echo "To deactivate:     deactivate"
echo ""