"""Test file to verify development environment setup.

This module contains basic tests to ensure the development environment
is configured correctly and all required dependencies are available.
"""

import sys
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.11 or higher."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version_info}"


def test_core_dependencies_importable():
    """Test that core production dependencies can be imported."""
    try:
        import fastapi
        import boto3
        import openai
        import pydantic
        import httpx
    except ImportError as e:
        raise AssertionError(f"Core dependency missing: {e}") from e


def test_development_tools_available():
    """Test that development tools are available in PATH."""
    import shutil

    tools = ["black", "ruff", "mypy"]
    missing_tools = []

    for tool in tools:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        raise AssertionError(
            f"Development tools not found in PATH: {', '.join(missing_tools)}"
        )


def test_project_structure_exists():
    """Verify basic project directory structure exists."""
    project_root = Path(__file__).parent.parent
    required_dirs = [
        project_root / "src",
        project_root / "tests",
        project_root / "_docs",
    ]

    missing_dirs = [str(d) for d in required_dirs if not d.exists()]

    if missing_dirs:
        raise AssertionError(f"Required directories missing: {', '.join(missing_dirs)}")


def test_configuration_files_exist():
    """Verify essential configuration files exist."""
    project_root = Path(__file__).parent.parent
    required_files = [
        project_root / "requirements.txt",
        project_root / "requirements-dev.txt",
        project_root / ".env.example",
        project_root / "pyproject.toml",
    ]

    missing_files = [str(f) for f in required_files if not f.exists()]

    if missing_files:
        raise AssertionError(f"Required files missing: {', '.join(missing_files)}")

