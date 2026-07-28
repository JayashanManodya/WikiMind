"""Text cleaning module to remove noise from extracted document text."""

import re


def clean_text(raw_text: str) -> str:
    """Clean raw extracted document text before Wiki generation.

    Applies:
    - Normalization of line breaks & whitespace
    - Stripping repetitive headers, footers, page numbers (e.g. 'Page X of Y')
    - Unifying punctuation and weird unicode whitespace
    """
    if not raw_text:
        return ""

    text = raw_text

    # Replace non-breaking spaces and special whitespace with standard space
    text = re.sub(r'[\r\t\f\v]', ' ', text)
    text = re.sub(r'\u00a0', ' ', text)

    # Remove header/footer line patterns like "Page 1 of 10", "Page 1", "--- 1 ---"
    text = re.sub(r'(?i)^\s*(page\s+\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+|---\s*\d+\s*---)\s*$', '', text, flags=re.MULTILINE)

    # Replace 3 or more consecutive newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Clean multiple spaces within lines
    text = re.sub(r'[ ]{2,}', ' ', text)

    return text.strip()
