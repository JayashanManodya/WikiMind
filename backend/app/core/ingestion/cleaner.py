"""Stage 3: Cleaning & Normalization Engine.

Performs rule-based deterministic cleaning and normalization on parsed Markdown
before any AI reasoning.
Removes boilerplate, page numbers, duplicate paragraphs, repeated headers/footers,
navigation links, advertisements, and empty sections.
Fixes OCR artifacts, broken line paragraphs, spacing errors, and encoding issues.
Normalizes headings, bullet lists, tables, and whitespace while preserving 100% meaning.
"""

import re
import unicodedata
from typing import Dict, Any, List, Set


NAVIGATION_PATTERNS = [
    r"(?i)^\s*back\s+to\s+top\s*$",
    r"(?i)^\s*table\s+of\s+contents\s*$",
    r"(?i)^\s*previous\s+page\s*\|\s*next\s+page\s*$",
    r"(?i)^\s*click\s+here\s+to\s+.*$",
    r"(?i)^\s*share\s+on\s+(facebook|twitter|linkedin)\s*$",
    r"(?i)^\s*all\s+rights\s+reserved\s*$"
]

PAGE_NUMBER_PATTERNS = [
    r"(?i)^\s*page\s+\d+\s*(of\s*\d+)?\s*$",
    r"^\s*-\s*\d+\s*-\s*$",
    r"^\s*\d+\s*$"
]

ADVERTISEMENT_PATTERNS = [
    r"(?i)^\s*advertisement\s*$",
    r"(?i)^\s*sponsored\s+content\s*$",
    r"(?i)^\s*subscribe\s+to\s+our\s+newsletter\s*$"
]


def clean_and_normalize_markdown(parsed_output: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize document markdown from Stage 2.

    Args:
        parsed_output: Dict containing full_markdown, pages, filename, etc.

    Returns:
        Dict containing:
            - original_markdown: Input full_markdown
            - cleaned_markdown: Cleaned, normalized markdown text
            - cleaning_stats: Dict of removed lines, fixed paragraphs, etc.
    """
    raw_md = parsed_output.get("full_markdown", "")
    
    # 1. Fix encoding problems and normalize unicode
    text = unicodedata.normalize("NFC", raw_md)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Fix OCR artifacts & bad spacing
    text = _fix_ocr_and_spacing(text)

    # 3. Process line by line for structural cleaning
    lines = text.split("\n")
    cleaned_lines: List[str] = []
    seen_paragraphs: Set[str] = set()
    header_footer_counts: Dict[str, int] = {}

    # Count occurrences of short lines for repeated header/footer detection
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) < 80:
            header_footer_counts[stripped] = header_footer_counts.get(stripped, 0) + 1

    total_lines = len(lines)
    repeated_threshold = max(3, int(parsed_output.get("total_pages", 1) * 0.7))

    for line in lines:
        stripped = line.strip()

        # Remove empty lines excess later
        if not stripped:
            cleaned_lines.append("")
            continue

        # Filter repeated headers / footers
        if header_footer_counts.get(stripped, 0) >= repeated_threshold and len(stripped) < 80 and not stripped.startswith("#"):
            continue

        # Filter page numbers
        if any(re.match(pat, stripped) for pat in PAGE_NUMBER_PATTERNS):
            continue

        # Filter navigation text
        if any(re.match(pat, stripped) for pat in NAVIGATION_PATTERNS):
            continue

        # Filter advertisements
        if any(re.match(pat, stripped) for pat in ADVERTISEMENT_PATTERNS):
            continue

        # Filter duplicate paragraphs (exact match for paragraphs > 40 chars)
        if len(stripped) > 40:
            para_key = re.sub(r"\s+", " ", stripped.lower())
            if para_key in seen_paragraphs:
                continue
            seen_paragraphs.add(para_key)

        cleaned_lines.append(line)

    # 4. Rejoin broken paragraphs & normalize whitespace
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = _rejoin_broken_paragraphs(cleaned_text)
    cleaned_text = _normalize_markdown_elements(cleaned_text)
    cleaned_text = _remove_empty_sections(cleaned_text)

    return {
        "filename": parsed_output.get("filename", "document"),
        "original_markdown": raw_md,
        "cleaned_markdown": cleaned_text.strip(),
        "cleaning_stats": {
            "original_char_count": len(raw_md),
            "cleaned_char_count": len(cleaned_text),
            "unique_paragraphs": len(seen_paragraphs)
        }
    }


def _fix_ocr_and_spacing(text: str) -> str:
    """Fix common OCR misreadings, bad spacing, and tabs."""
    # Replace tab characters with 4 spaces
    text = text.replace("\t", "    ")
    
    # Fix multiple spaces within lines (excluding list indentation)
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        if line.lstrip().startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
            indent = len(line) - len(line.lstrip())
            content = re.sub(r" +", " ", line.lstrip())
            fixed_lines.append(" " * indent + content)
        else:
            fixed_lines.append(re.sub(r" +", " ", line))

    text = "\n".join(fixed_lines)

    # Fix OCR broken hyphens at line ends (e.g. "com- \n pany" -> "company")
    text = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", text)

    return text


def _rejoin_broken_paragraphs(text: str) -> str:
    """Rejoin lines that were split mid-sentence by page wraps or line breaks."""
    lines = text.split("\n")
    rejoined: List[str] = []
    
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if not stripped or stripped.startswith(("#", "-", "*", "|", ">", "```", "1.", "2.", "3.")):
            rejoined.append(line)
            idx += 1
            continue

        # If current line does not end with sentence-ending punctuation and next line is standard text
        if idx + 1 < len(lines):
            next_line = lines[idx + 1]
            next_stripped = next_line.strip()

            if (
                next_stripped
                and not next_stripped.startswith(("#", "-", "*", "|", ">", "```", "1.", "2.", "3."))
                and not stripped.endswith((".", ":", "?", "!", ";", '"', "'"))
                and next_stripped[0].islower()
            ):
                # Join lines with space
                joined_line = line.rstrip() + " " + next_stripped.lstrip()
                lines[idx + 1] = joined_line
                idx += 1
                continue

        rejoined.append(line)
        idx += 1

    return "\n".join(rejoined)


def _normalize_markdown_elements(text: str) -> str:
    """Normalize headers, bullet lists, tables, and blank line spacing."""
    lines = text.split("\n")
    normalized: List[str] = []

    for line in lines:
        # Standardize bullet list syntax (* or + -> -)
        if re.match(r"^\s*[\*\+]\s+", line):
            line = re.sub(r"^(\s*)[\*\+]\s+", r"\1- ", line)

        # Standardize header spacing (#Header -> # Header)
        if re.match(r"^#{1,6}[^#\s]", line):
            line = re.sub(r"^(#{1,6})([^#\s])", r"\1 \2", line)

        normalized.append(line)

    # Collapse more than 2 consecutive blank lines into 2
    text = "\n".join(normalized)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _remove_empty_sections(text: str) -> str:
    """Remove header lines followed immediately by another header or end of document with no body text."""
    lines = text.split("\n")
    final_lines: List[str] = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if stripped.startswith("#"):
            # Check if next non-empty line is also a header of equal or higher level
            next_idx = idx + 1
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1

            if next_idx < len(lines):
                next_stripped = lines[next_idx].strip()
                if next_stripped.startswith("#") and _header_level(next_stripped) <= _header_level(stripped):
                    # Skip empty header
                    idx = next_idx
                    continue

        final_lines.append(line)
        idx += 1

    return "\n".join(final_lines)


def _header_level(header_line: str) -> int:
    match = re.match(r"^(#{1,6})\s", header_line)
    return len(match.group(1)) if match else 1
