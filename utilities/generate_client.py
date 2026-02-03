#!/usr/bin/env python3
"""
Script to generate GraphQL client and fix nullable fields.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return True if successful."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    """Generate client and fix nullable fields."""
    # Activate virtual environment
    venv_path = "../environment/bin/activate"
    if os.path.exists(venv_path):
        print("Activating virtual environment...")
        # We need to source the environment, but subprocess doesn't support source
        # So we'll run the commands with the full path
        python_cmd = "environment/bin/python"
        ariadne_cmd = "environment/bin/ariadne-codegen"
    else:
        python_cmd = sys.executable
        ariadne_cmd = "ariadne-codegen"

    # Generate the client
    if not run_command([ariadne_cmd]):
        print("Failed to generate client")
        return 1

    # Fix nullable fields
    if not run_command([python_cmd, "fix_nullable_fields.py"]):
        print("Failed to fix nullable fields")
        return 1

    print("Client generation completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())