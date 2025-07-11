#!/usr/bin/env python3
"""
Test script to verify the Wasabi File Manager starts correctly
"""

import sys
import os
import subprocess
import time

def test_startup():
    """Test that the application starts without errors"""
    print("Testing Wasabi File Manager startup...")
    
    # Start the application in a subprocess
    try:
        # Start the application
        proc = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for it to start
        time.sleep(2)
        
        # Check if it's still running (no immediate crash)
        if proc.poll() is None:
            print("✓ Application started successfully")
            proc.terminate()
            proc.wait()
            return True
        else:
            # Process has exited, check for errors
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                print(f"✗ Application crashed with return code {proc.returncode}")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
            else:
                print("✓ Application ran and exited normally")
                return True
                
    except Exception as e:
        print(f"✗ Failed to start application: {e}")
        return False

if __name__ == "__main__":
    success = test_startup()
    sys.exit(0 if success else 1)
