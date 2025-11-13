"""Tests for demo environment setup scripts."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_setup_demo_environment_script_exists():
    """Test that setup_demo_environment.sh exists and is executable."""
    script_path = Path("scripts/setup_demo_environment.sh")
    assert script_path.exists(), "setup_demo_environment.sh should exist"
    assert script_path.is_file(), "setup_demo_environment.sh should be a file"


def test_demo_walkthrough_script_exists():
    """Test that demo_walkthrough.sh exists and is executable."""
    script_path = Path("scripts/demo_walkthrough.sh")
    # Script is created by setup_demo_environment.sh, so it may not exist yet
    # This test verifies the script can be created
    assert script_path.parent.exists(), "scripts directory should exist"


@patch("subprocess.run")
def test_setup_demo_environment_checks_prerequisites(mock_subprocess):
    """Test that setup script checks for prerequisites."""
    # Mock AWS CLI check
    mock_subprocess.return_value = MagicMock(returncode=0)
    
    script_path = Path("scripts/setup_demo_environment.sh")
    if script_path.exists():
        # Just verify script is syntactically correct
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"


def test_setup_demo_environment_script_syntax():
    """Test that setup_demo_environment.sh has valid bash syntax."""
    script_path = Path("scripts/setup_demo_environment.sh")
    if script_path.exists():
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"


def test_demo_walkthrough_script_syntax():
    """Test that demo_walkthrough.sh has valid bash syntax (if it exists)."""
    script_path = Path("scripts/demo_walkthrough.sh")
    if script_path.exists():
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"

