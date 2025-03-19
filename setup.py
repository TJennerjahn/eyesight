from setuptools import setup, find_packages

setup(
    name="eyesight-reminder",
    version="0.1.0",
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
    url="https://github.com/tjennerjahn/eyesight-reminder",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
)

