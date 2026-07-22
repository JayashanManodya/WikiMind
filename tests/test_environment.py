import sys
import os
import subprocess
from pathlib import Path
import pytest
from dotenv import load_dotenv

def test_python_runs():
    """Verify Python interpreter runs and matches minimum version 3.10+"""
    assert sys.version_info >= (3, 10), "Python version must be 3.10 or higher"

def test_virtual_environment_active():
    """Verify Python is executing from inside the project virtual environment (.venv)"""
    executable = sys.executable.lower()
    assert ".venv" in executable, f"Python is not running inside .venv! Path: {sys.executable}"

def test_git_repository_initialized():
    """Verify Git repository is initialized and valid"""
    repo_dir = Path(__file__).parent.parent
    git_dir = repo_dir / ".git"
    assert git_dir.exists(), f"Git directory does not exist at {git_dir}"
    
    result = subprocess.run(["git", "status"], capture_output=True, text=True, cwd=repo_dir)
    assert result.returncode == 0, f"Git status command failed: {result.stderr}"

def test_environment_variables_load():
    """Verify environment variables load correctly from .env"""
    repo_dir = Path(__file__).parent.parent
    env_file = repo_dir / ".env"
    assert env_file.exists(), ".env file does not exist!"
    
    load_dotenv(env_file, override=True)
    assert os.getenv("APP_NAME") == "WikiMind", "APP_NAME not loaded correctly from .env"
    assert os.getenv("PORT") == "8000", "PORT not loaded correctly from .env"
    assert os.getenv("LLM_PROVIDER") is not None, "LLM_PROVIDER not set in .env"

def test_dependencies_installed():
    """Verify required core dependencies are installed and importable"""
    import fastapi
    import uvicorn
    import pydantic
    import dotenv
    
    assert fastapi.__version__ is not None
    assert uvicorn.__version__ is not None
    assert pydantic.__version__ is not None
    assert callable(dotenv.load_dotenv)
