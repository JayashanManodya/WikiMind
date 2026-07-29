"""Central Path Manager for WikiLLM.

Resolves normalized directory paths for per-user data storage,
preventing duplicate path nesting (e.g. backend/backend) and ensuring
a single, unified per-user directory structure under wiki/users/{user_id}/.
"""

import os
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
    """Get the base wiki directory root (IKMS_WikiLLM/wiki)."""
    root = get_project_root()
    wiki_dir = root / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    return wiki_dir

def get_user_wiki_dir(user_id: str) -> Path:
    """Get unified per-user wiki directory root (wiki/users/{user_id}/).
    
    Structure:
    wiki/users/{user_id}/
    ├── raw_documents/        # Original uploaded source files
    ├── metadata/             # JSON enrichment metadata
    ├── Index.md              # Index page
    ├── index.json            # Index catalog
    ├── graph.json            # Knowledge Graph catalog
    ├── log.md                # Execution log
    └── [Wiki_Pages].md       # Markdown topic pages
    """
    clean_user = user_id.strip().replace(" ", "_")
    user_dir = get_base_wiki_dir() / "users" / clean_user
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def get_user_raw_docs_dir(user_id: str) -> Path:
    """Get raw document storage directory for a specific user (wiki/users/{user_id}/raw_documents)."""
    raw_dir = get_user_wiki_dir(user_id) / "raw_documents"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

def get_user_metadata_dir(user_id: str) -> Path:
    """Get metadata directory for a specific user (wiki/users/{user_id}/metadata)."""
    meta_dir = get_user_wiki_dir(user_id) / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    return meta_dir
