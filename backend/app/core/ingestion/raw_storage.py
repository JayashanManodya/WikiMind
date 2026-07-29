"""Stage 1: Raw Document Storage Manager.

Ensures original uploaded files (PDF, DOCX, HTML, Markdown, Images, PPTX)
are stored unchanged as immutable source documents.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Union


ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "html": "text/html",
    "htm": "text/html",
    "md": "text/markdown",
    "markdown": "text/markdown",
    "txt": "text/plain",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "ppt": "application/vnd.ms-powerpoint"
}


from ..paths import get_user_raw_docs_dir


def store_raw_document(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    base_dir: Union[str, Path, None] = None
) -> Dict[str, Any]:
    """Store original file unchanged as an immutable source document under wiki/users/{user_id}/raw_documents.

    Args:
        file_bytes: Raw binary bytes of the document.
        filename: Original file name.
        user_id: ID of the user performing the upload.
        base_dir: Optional custom directory path override.

    Returns:
        Dict containing document metadata including immutable path, sha256, and size.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS.keys()))}"
        )

    # Compute immutable SHA-256 hash
    doc_hash = hashlib.sha256(file_bytes).hexdigest()
    
    if base_dir:
        target_dir = Path(base_dir) / user_id
    else:
        target_dir = get_user_raw_docs_dir(user_id)
        
    target_dir.mkdir(parents=True, exist_ok=True)

    sanitized_filename = filename.replace(" ", "_")
    immutable_filename = f"{doc_hash[:12]}_{sanitized_filename}"
    immutable_path = target_dir / immutable_filename

    # Write binary content unchanged (immutable)
    immutable_path.write_bytes(file_bytes)

    return {
        "filename": filename,
        "extension": ext,
        "mime_type": ALLOWED_EXTENSIONS.get(ext, "application/octet-stream"),
        "user_id": user_id,
        "size_bytes": len(file_bytes),
        "sha256": doc_hash,
        "immutable_path": str(immutable_path.resolve()),
        "is_immutable": True
    }
