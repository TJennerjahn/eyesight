# Release Process

This document outlines the steps to create a new release of eyesight-reminder and publish it to PyPI.

## Prerequisites

Ensure you have the following installed:
- Python 3.8+
- build (`pip install build`)
- twine (`pip install twine`)

## Steps to release

1. Update version number in `eyesight_reminder/__init__.py`
2. Update CHANGELOG.md with the new version and changes
3. Commit these changes:
   ```bash
   git add eyesight_reminder/__init__.py CHANGELOG.md
   git commit -m "Bump version to x.y.z"
   ```

4. Tag the release:
   ```bash
   git tag -a vx.y.z -m "Version x.y.z"
   git push origin vx.y.z
   ```

5. Build the distribution packages:
   ```bash
   python -m build
   ```

6. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```

## AppImage Compatibility Notes

When packaging as an AppImage:
- The application looks for resources relative to the script path
- Resource files are included via `package_data` in setup.py
- The same PyPI package can be used as a base for creating an AppImage