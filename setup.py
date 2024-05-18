from setuptools import setup, find_packages

setup(
    name='eyesight',
    version='0.1.0',
    description='A PyQt5 systray application to remind you to take breaks.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Tobias Jennerjahn',
    author_email='tobias@jennerjahn.xyz',
    url='https://github.com/tjennerjahn/eyesight',
    packages=find_packages(),
    install_requires=[
        'PyQt5',
    ],
    entry_points={
        'console_scripts': [
            'eyesight=eyesight.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['icon.png'],
    },
)
