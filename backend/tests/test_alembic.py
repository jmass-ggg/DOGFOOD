"""Unit tests for Alembic migration infrastructure."""

import configparser
import os
from pathlib import Path


class TestAlembicSetup:
    """Tests for Alembic migration setup and configuration."""

    def test_alembic_ini_exists(self):
        """Test that alembic.ini exists in the backend directory."""
        backend_dir = Path(__file__).parent.parent
        alembic_ini_path = backend_dir / "alembic.ini"
        assert alembic_ini_path.exists(), "alembic.ini file does not exist"

    def test_alembic_ini_is_valid(self):
        """Test that alembic.ini is a valid configuration file with required sections."""
        backend_dir = Path(__file__).parent.parent
        alembic_ini_path = backend_dir / "alembic.ini"
        
        # Parse the alembic.ini file
        config = configparser.ConfigParser()
        config.read(alembic_ini_path)
        
        # Check that required sections exist
        assert "alembic" in config, "alembic.ini missing [alembic] section"
        
        # Check that required settings exist in [alembic] section
        alembic_section = config["alembic"]
        assert "script_location" in alembic_section, "alembic.ini missing script_location"
        
        # Verify script_location points to migrations directory
        script_location = alembic_section["script_location"]
        assert script_location == "migrations", f"script_location should be 'migrations', got '{script_location}'"

    def test_migrations_directory_exists(self):
        """Test that migrations directory exists."""
        backend_dir = Path(__file__).parent.parent
        migrations_dir = backend_dir / "migrations"
        assert migrations_dir.exists(), "migrations directory does not exist"
        assert migrations_dir.is_dir(), "migrations path exists but is not a directory"

    def test_migrations_directory_structure(self):
        """Test that migrations directory has the expected structure."""
        backend_dir = Path(__file__).parent.parent
        migrations_dir = backend_dir / "migrations"
        
        # Check for required files and directories
        required_files = ["env.py", "script.py.mako", "README"]
        for file_name in required_files:
            file_path = migrations_dir / file_name
            assert file_path.exists(), f"migrations/{file_name} does not exist"
        
        # Check for versions directory
        versions_dir = migrations_dir / "versions"
        assert versions_dir.exists(), "migrations/versions directory does not exist"
        assert versions_dir.is_dir(), "migrations/versions exists but is not a directory"

    def test_migrations_env_py_imports(self):
        """Test that env.py can be imported without errors."""
        backend_dir = Path(__file__).parent.parent
        migrations_dir = backend_dir / "migrations"
        env_py_path = migrations_dir / "env.py"
        
        # Read the env.py file
        env_py_content = env_py_path.read_text()
        
        # Check that env.py imports Base from app.models
        assert "from app.models import Base" in env_py_content, \
            "env.py should import Base from app.models"
        
        # Check that env.py sets target_metadata
        assert "target_metadata = Base.metadata" in env_py_content, \
            "env.py should set target_metadata to Base.metadata"
