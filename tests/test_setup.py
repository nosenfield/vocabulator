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
    """Verify complete project directory structure exists per architecture.md."""
    project_root = Path(__file__).parent.parent
    
    # Core source directories
    required_dirs = [
        # Source directories
        project_root / "src",
        project_root / "src" / "api",
        project_root / "src" / "api" / "routes",
        project_root / "src" / "api" / "models",
        project_root / "src" / "api" / "middleware",
        project_root / "src" / "processing",
        project_root / "src" / "ai",
        project_root / "src" / "ai" / "prompts",
        project_root / "src" / "data",
        project_root / "src" / "data" / "models",
        project_root / "src" / "data" / "repositories",
        project_root / "src" / "vocabulary",
        project_root / "src" / "vocabulary" / "corpus",
        project_root / "src" / "utils",
        project_root / "src" / "frontend",
        project_root / "src" / "frontend" / "templates",
        project_root / "src" / "frontend" / "static" / "css",
        project_root / "src" / "frontend" / "static" / "js",
        # Test directories
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "fixtures",
        project_root / "tests" / "fixtures" / "sample_transcripts",
        project_root / "tests" / "mocks",
        # Infrastructure directories
        project_root / "infrastructure",
        project_root / "infrastructure" / "cloudformation",
        project_root / "infrastructure" / "docker",
    ]

    missing_dirs = [str(d) for d in required_dirs if not d.exists()]

    if missing_dirs:
        raise AssertionError(f"Required directories missing: {', '.join(missing_dirs)}")


def test_python_packages_have_init_files():
    """Verify all Python packages have __init__.py files."""
    project_root = Path(__file__).parent.parent
    
    python_packages = [
        project_root / "src",
        project_root / "src" / "api",
        project_root / "src" / "api" / "routes",
        project_root / "src" / "api" / "models",
        project_root / "src" / "api" / "middleware",
        project_root / "src" / "processing",
        project_root / "src" / "ai",
        project_root / "src" / "ai" / "prompts",
        project_root / "src" / "data",
        project_root / "src" / "data" / "models",
        project_root / "src" / "data" / "repositories",
        project_root / "src" / "vocabulary",
        project_root / "src" / "vocabulary" / "corpus",
        project_root / "src" / "utils",
        project_root / "src" / "frontend",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "fixtures",
        project_root / "tests" / "mocks",
    ]
    
    missing_init_files = []
    for package_dir in python_packages:
        init_file = package_dir / "__init__.py"
        if package_dir.exists() and not init_file.exists():
            missing_init_files.append(str(init_file))
    
    if missing_init_files:
        raise AssertionError(
            f"Missing __init__.py files: {', '.join(missing_init_files)}"
        )


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

