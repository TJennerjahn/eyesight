#!/usr/bin/env python3
"""
Test script to verify package resources are properly included.
Run this after installing the package with pip to verify everything works.
"""

import os
import sys
import importlib.resources
import importlib.util

def verify_package_installation():
    """Verify that the eyesight-reminder package is properly installed."""
    print("Checking eyesight-reminder package installation...")
    
    # Check if the package is importable
    try:
        import eyesight_reminder
        print(f"✓ Package eyesight_reminder can be imported")
        print(f"  Version: {eyesight_reminder.__version__}")
        print(f"  Package location: {os.path.dirname(eyesight_reminder.__file__)}")
    except ImportError:
        print("✗ Failed to import eyesight_reminder package")
        return False
    
    # Check if the main module is importable
    try:
        from eyesight_reminder import main
        print("✓ Module eyesight_reminder.main can be imported")
    except ImportError:
        print("✗ Failed to import eyesight_reminder.main module")
        return False
    
    # Check if resources are included
    try:
        resources_dir = os.path.join(os.path.dirname(eyesight_reminder.__file__), "resources")
        if os.path.exists(resources_dir):
            icon_path = os.path.join(resources_dir, "icon.png")
            if os.path.exists(icon_path):
                print(f"✓ Icon file found at {icon_path}")
            else:
                print(f"✗ Icon file not found at {icon_path}")
                return False
        else:
            print(f"✗ Resources directory not found at {resources_dir}")
            return False
    except Exception as e:
        print(f"✗ Error checking resources: {e}")
        return False
    
    # Check if entry point is installed
    import shutil
    eyesight_bin = shutil.which("eyesight-reminder")
    if eyesight_bin:
        print(f"✓ eyesight-reminder command is available at {eyesight_bin}")
    else:
        print("✗ eyesight-reminder command not found in PATH")
        print("  This might be normal if installed with --user and user bin directory is not in PATH")
    
    print("\nPackage verification complete: All checks passed!")
    return True

if __name__ == "__main__":
    success = verify_package_installation()
    sys.exit(0 if success else 1)