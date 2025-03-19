from setuptools import setup, find_packages
import os
import re

# Read the README.md for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Get version from __init__.py
with open("eyesight_reminder/__init__.py", encoding="utf-8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setup(
    name="eyesight-reminder",
    version=version,
    packages=find_packages(),
    install_requires=["PyQt5"],
    entry_points={
        "console_scripts": [
            "eyesight-reminder=eyesight_reminder.main:main",
        ],
    },
    package_data={
        "eyesight_reminder": ["resources/*.png"],
    },
    author="Tobias Jennerjahn",
    author_email="tobias@jennerjahn.xyz",
    description="A simple utility to remind you to take regular eye breaks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tjennerjahn/eyesight-reminder",
    project_urls={
        "Bug Tracker": "https://github.com/tjennerjahn/eyesight-reminder/issues",
    },
    keywords="eyesight, eye-care, reminder, health, 20-20-20, utility",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.8",
    license="MIT",
)

