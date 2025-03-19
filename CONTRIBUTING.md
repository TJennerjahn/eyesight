# Contributing to eyesight-reminder

Thank you for considering contributing to eyesight-reminder! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally
```bash
git clone https://github.com/your-username/eyesight-reminder.git
cd eyesight-reminder
```

3. Set up a development environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
```

## Development Workflow

1. Create a branch for your work
```bash
git checkout -b your-feature-branch
```

2. Make your changes and ensure they work as expected

3. Run tests and lint your code
```bash
pytest
flake8
```

4. Commit your changes with descriptive commit messages

5. Push your branch and create a pull request

## Pull Request Guidelines

- Keep your changes focused and related to a single issue/feature
- Include a clear description of what your changes do
- Update documentation as needed
- Ensure your code follows the project's style and passes linting
- Add tests for new functionality

## Building the Package

To build the package locally:

```bash
python -m build
```

This will create both source and wheel distributions in the `dist/` directory.

## Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add comments for complex sections of code
- Keep functions and methods small and focused