"""
Unit tests for Docker infrastructure.

Validates: Requirements 11.1
"""
import os
from pathlib import Path


def test_dockerfile_exists():
    """Test that Dockerfile exists in the backend directory."""
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile should exist in backend directory"


def test_dockerfile_is_valid():
    """Test that Dockerfile contains required elements for a valid Python FastAPI application."""
    dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
    
    with open(dockerfile_path, "r") as f:
        content = f.read()
    
    # Verify Python 3.12+ base image
    assert "python:3.12" in content.lower(), "Dockerfile should use Python 3.12+ base image"
    
    # Verify working directory is set
    assert "WORKDIR" in content, "Dockerfile should set a working directory"
    
    # Verify dependencies are installed from pyproject.toml
    assert "pyproject.toml" in content, "Dockerfile should copy pyproject.toml"
    assert "pip install" in content, "Dockerfile should install Python dependencies"
    
    # Verify port is exposed
    assert "EXPOSE" in content, "Dockerfile should expose a port"
    
    # Verify uvicorn is configured as entrypoint
    assert "uvicorn" in content.lower(), "Dockerfile should use uvicorn as entrypoint"
    assert "app.main:app" in content or "app.main" in content, "Dockerfile should reference the FastAPI app"
