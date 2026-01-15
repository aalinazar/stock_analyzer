#!/usr/bin/env python3
"""
Simple script to run tests with the correct Python environment.
This ensures tests run with the virtual environment regardless of how they're invoked.
"""

import subprocess
import sys
import os

def main():
    """Run tests using the virtual environment's pytest"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the virtual environment's pytest
    venv_pytest = os.path.join(script_dir, "venv", "bin", "pytest")
    
    # Check if virtual environment pytest exists
    if not os.path.exists(venv_pytest):
        print("Error: Virtual environment not found or pytest not installed.")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run pytest with the tests directory
    cmd = [venv_pytest, "tests/", "-v"]
    
    try:
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
