"""Stage 2: LlamaParse & Multi-Format Document Parser.

Replaces PyMuPDF extraction with LlamaParse for structured Markdown extraction.
Extracts headings, hierarchy, paragraphs, lists, tables, captions, footnotes,
images, page numbers, and document metadata into structured Markdown.
Provides robust fallback processing for PDF, DOCX, HTML, MD, Images, and PPTX.
"""

import os
import io
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
import docx

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import pptx
except ImportError:
    pptx = None

from ..config import get_settings


def parse_with_llamaparse_or_fallback(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Parse raw document bytes into structured Markdown representation.

    Args:
        file_bytes: Raw bytes of the document.
        filename: Document filename.
        api_key: Optional LlamaCloud API Key. If not provided, checks app settings / ENV.

    Returns:
        Dict containing:
            - filename: Original filename
            - total_pages: Total extracted page count
            - pages: List of {"page_number": int, "markdown": str}
            - full_markdown: Complete structured document Markdown
            - parser_used: "LlamaParse" or "FallbackParser"
            - metadata: Extracted document metadata
    """
    settings = get_settings()
    llama_key = api_key or os.environ.get("LLAMA_CLOUD_API_KEY") or getattr(settings, "llama_cloud_api_key", "")

    if llama_key and llama_key.strip() and not llama_key.startswith("placeholder"):
        try:
            return _parse_with_llamaparse(file_bytes, filename, llama_key)
        except Exception as e:
            # Fallback on LlamaParse API error
            pass

    return _fallback_structured_parse(file_bytes, filename)


def _parse_with_llamaparse(file_bytes: bytes, filename: str, api_key: str) -> Dict[str, Any]:
    """Parse document using LlamaParse SDK."""
    from llama_parse import LlamaParse

    ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=False
        )
        extra_docs = parser.load_data(tmp_path)
        
        pages = []
        full_md_parts = []
        for idx, doc in enumerate(extra_docs):
            md_text = doc.text or ""
            pages.append({
                "page_number": idx + 1,
                "markdown": md_text
            })
            full_md_parts.append(md_text)

        full_markdown = "\n\n---\n\n".join(full_md_parts).strip()
        return {
            "filename": filename,
            "total_pages": len(pages),
            "pages": pages,
            "full_markdown": full_markdown,
            "parser_used": "LlamaParse",
            "metadata": {
                "format": ext.lstrip("."),
                "pages_count": len(pages)
            }
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _fallback_structured_parse(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Fallback structured markdown parser supporting PDF, DOCX, HTML, MD, PPTX, and Images."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _fallback_parse_pdf(file_bytes, filename)
    elif ext in ["docx", "doc"]:
        return _fallback_parse_docx(file_bytes, filename)
    elif ext in ["html", "htm"]:
        return _fallback_parse_html(file_bytes, filename)
    elif ext in ["md", "markdown", "txt"]:
        return _fallback_parse_text(file_bytes, filename)
    elif ext in ["pptx", "ppt"]:
        return _fallback_parse_pptx(file_bytes, filename)
    elif ext in ["png", "jpg", "jpeg", "webp"]:
        return _fallback_parse_image(file_bytes, filename)
    else:
        return _fallback_parse_text(file_bytes, filename)


def _fallback_parse_pdf(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract structured Markdown from PDF using PyMuPDF (fitz)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: List[Dict[str, Any]] = []
    full_md_parts: List[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text") or ""
        
        # Structure headers vs paragraphs basic heuristic
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        formatted_lines = []
        for line in lines:
            if "\t" in line:
                cells = [c.strip() for c in line.split("\t") if c.strip()]
                formatted_lines.append(" | ".join(cells))
            elif len(line) < 60 and not line.endswith((".", ":", ";", ",")) and not line.startswith(("#", "-", "*", "|")):
                formatted_lines.append(f"### {line}")
            else:
                formatted_lines.append(line)
        
        page_md = "\n\n".join(formatted_lines)
        pages.append({
            "page_number": page_num + 1,
            "markdown": page_md
        })
        full_md_parts.append(page_md)

    doc.close()
    full_markdown = "\n\n---\n\n".join(full_md_parts).strip()

    return {
        "filename": filename,
        "total_pages": len(pages),
        "pages": pages,
        "full_markdown": full_markdown,
        "parser_used": "FallbackPDFParser",
        "metadata": {"total_pages": len(pages)}
    }


def _fallback_parse_docx(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract structured Markdown from DOCX including headings and tables."""
    buffer = io.BytesIO(file_bytes)
    doc = docx.Document(buffer)
    md_parts: List[str] = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        
        style_name = p.style.name.lower() if p.style else ""
        if "heading 1" in style_name:
            md_parts.append(f"# {text}")
        elif "heading 2" in style_name:
            md_parts.append(f"## {text}")
        elif "heading 3" in style_name:
            md_parts.append(f"### {text}")
        elif "list" in style_name:
            md_parts.append(f"- {text}")
        else:
            md_parts.append(text)

    for table in doc.tables:
        if not table.rows:
            continue
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        md_table = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]
        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            md_table.append("| " + " | ".join(cells) + " |")
        md_parts.append("\n".join(md_table))

    full_markdown = "\n\n".join(md_parts).strip()
    return {
        "filename": filename,
        "total_pages": 1,
        "pages": [{"page_number": 1, "markdown": full_markdown}],
        "full_markdown": full_markdown,
        "parser_used": "FallbackDocxParser",
        "metadata": {"total_paragraphs": len(doc.paragraphs), "tables": len(doc.tables)}
    }


def _fallback_parse_html(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract Markdown from HTML using BeautifulSoup."""
    content = file_bytes.decode("utf-8", errors="replace")
    if BeautifulSoup:
        soup = BeautifulSoup(content, "html.parser")
        # Remove nav, script, style
        for s in soup(["script", "style", "nav", "footer", "header"]):
            s.decompose()
        text = soup.get_text(separator="\n\n").strip()
    else:
        text = content

    return {
        "filename": filename,
        "total_pages": 1,
        "pages": [{"page_number": 1, "markdown": text}],
        "full_markdown": text,
        "parser_used": "FallbackHTMLParser",
        "metadata": {}
    }


def _fallback_parse_text(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract Markdown from plain text or Markdown."""
    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = file_bytes.decode("latin-1", errors="replace")

    return {
        "filename": filename,
        "total_pages": 1,
        "pages": [{"page_number": 1, "markdown": content}],
        "full_markdown": content,
        "parser_used": "FallbackTextParser",
        "metadata": {}
    }


def _fallback_parse_pptx(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract Markdown from PPTX presentation slides."""
    if not pptx:
        return _fallback_parse_text(file_bytes, filename)

    prs = pptx.Presentation(io.BytesIO(file_bytes))
    pages = []
    full_md_parts = []

    for idx, slide in enumerate(prs.slides):
        slide_texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_texts.append(shape.text.strip())
        
        slide_md = f"## Slide {idx + 1}\n\n" + "\n\n".join(slide_texts)
        pages.append({"page_number": idx + 1, "markdown": slide_md})
        full_md_parts.append(slide_md)

    full_markdown = "\n\n---\n\n".join(full_md_parts).strip()
    return {
        "filename": filename,
        "total_pages": len(pages),
        "pages": pages,
        "full_markdown": full_markdown,
        "parser_used": "FallbackPPTXParser",
        "metadata": {"slide_count": len(pages)}
    }


def _fallback_parse_image(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Extract image placeholder metadata description."""
    size_kb = len(file_bytes) / 1024.0
    image_md = f"# Image Asset: {filename}\n\n**Format**: Image ({filename.rsplit('.', 1)[-1]})\n**Size**: {size_kb:.1f} KB\n"
    return {
        "filename": filename,
        "total_pages": 1,
        "pages": [{"page_number": 1, "markdown": image_md}],
        "full_markdown": image_md,
        "parser_used": "FallbackImageParser",
        "metadata": {"image_size_kb": size_kb}
    }
