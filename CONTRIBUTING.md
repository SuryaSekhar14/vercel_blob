# Contributing to vercel_blob

Thank you for your interest in contributing to vercel_blob! This document provides guidelines and setup instructions for development.

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/SuryaSekhar14/vercel_blob.git
cd vercel_blob
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

4. Install the package in editable mode:

```bash
pip install -e .
```

## Running Tests

1. Create a `.env` file in the root directory with your Vercel Blob Storage token:

```
BLOB_READ_WRITE_TOKEN=your_token_here
```

2. Run the test script:

```bash
python tests/custom_test_script.py
```

## Project Structure

- `requirements.txt`: Production dependencies only
- `requirements-dev.txt`: Development and testing dependencies
- `tests/`: Test files
- `vercel_blob/`: Main package code

## Making Changes

1. Create a new branch for your changes
2. Make your changes
3. Test your changes
4. Submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Add docstrings for new functions
- Keep the code simple and well-documented

## Questions?

If you have any questions, feel free to open an issue on GitHub.
