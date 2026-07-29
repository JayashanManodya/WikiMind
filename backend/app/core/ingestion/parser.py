"""Document parser supporting PDF, DOCX, HTML, MD, Images, and PPTX via LlamaParse and multi-format structured fallbacks."""

from typing import Dict, Any
from .llama_parser import parse_with_llamaparse_or_fallback


def parse_document_bytes(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Parse document bytes into structured Markdown representation.

    Args:
        file_bytes: Raw byte contents of the uploaded file.
        filename: Original filename (.pdf, .docx, .html, .md, .png, .jpg, .pptx).

    Returns:
        Dict containing filename, total_pages, pages, full_text, full_markdown.
    """
    parsed = parse_with_llamaparse_or_fallback(file_bytes, filename)
    
    # Structure pages with both 'text' and 'markdown' keys for full backwards compatibility
    pages_compat = []
    for p in parsed.get("pages", []):
        md = p.get("markdown", "")
        pages_compat.append({
            "page_number": p.get("page_number", 1),
            "text": md,
            "markdown": md
        })

    full_md = parsed.get("full_markdown", "")
    return {
        "filename": parsed.get("filename", filename),
        "total_pages": parsed.get("total_pages", len(pages_compat)),
        "pages": pages_compat,
        "full_text": full_md,
        "full_markdown": full_md,
        "parser_used": parsed.get("parser_used", "LlamaParse"),
        "metadata": parsed.get("metadata", {})
    }
