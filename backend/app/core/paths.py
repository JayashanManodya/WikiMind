"""Central Path Manager for WikiLLM.

Resolves normalized directory paths for per-user data storage,
preventing duplicate path nesting (e.g. backend/backend) and ensuring
a single, unified per-user directory structure under wiki/users/{user_id}/.
"""

import os
import tempfile
from pathlib import Path

def get_project_root() -> Path:
    """Find the root project directory (IKMS_WikiLLM)."""
    cwd = Path.cwd().resolve()
    if cwd.name == "backend":
        return cwd.parent
    if (cwd / "backend").exists():
        return cwd
    return cwd

def get_base_wiki_dir() -> Path:
    """Get the base wiki directory root."""
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return Path(tempfile.gettempdir()) / "wiki"
    root = get_project_root()
    return root / "wiki"


def get_user_wiki_dir(user_id: str) -> Path:
    """Get unified per-user wiki directory root (wiki/users/{user_id}/)."""
    clean_user = user_id.strip().replace(" ", "_")
    user_dir = get_base_wiki_dir() / "users" / clean_user
    return user_dir


def get_user_raw_docs_dir(user_id: str) -> Path:
    """Get raw document storage directory for a specific user (wiki/users/{user_id}/raw_documents)."""
    raw_dir = get_user_wiki_dir(user_id) / "raw_documents"
    return raw_dir

def get_user_metadata_dir(user_id: str) -> Path:
    """Get metadata directory for a specific user (wiki/users/{user_id}/metadata)."""
    meta_dir = get_user_wiki_dir(user_id) / "metadata"
    return meta_dir

