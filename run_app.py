#!/usr/bin/env python3
"""
Stock Analyzer Application Launcher

Run this script to start the Stock Analyzer application.
"""

import sys
import os
import subprocess

def main():
    """Main launcher function"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the script directory to Python path
    sys.path.insert(0, script_dir)
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Run the Streamlit app
    try:
        subprocess.run([
            "python", "-m", "streamlit", "run", "src/app.py",
            "--server.headless", "false",
            "--server.port", "8501"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
