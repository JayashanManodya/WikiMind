import os
import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from collections import Counter
from fastapi import HTTPException, status

from BackEnd.schemas import CleanedPage, CleanedDocumentResponse
from BackEnd.services.parser_service import parser_service
from BackEnd.services.metadata_service import metadata_service

BACKEND_DIR = Path(__file__).resolve().parent.parent

class TextCleaner:
    def __init__(self, cleaned_dir: str = "./BackEnd/storage/cleaned"):
        if isinstance(cleaned_dir, str) and cleaned_dir.startswith("./"):
            clean_rel = cleaned_dir[2:]
            if clean_rel.startswith("BackEnd/"):
                self.cleaned_dir = (BACKEND_DIR.parent / clean_rel).resolve()
            else:
                self.cleaned_dir = (BACKEND_DIR / "storage" / clean_rel.replace("storage/", "")).resolve()
        else:
            self.cleaned_dir = Path(cleaned_dir).resolve()
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)

    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters to standard UTF-8 (NFKC format), replacing smart quotes and em-dashes"""
        if not text:
            return ""
        
        # Replace Windows-1252 / WinAnsi curly quote and dash characters before NFKC
        winansi_replacements = {
            "\u0091": "'", "\u0092": "'",   # Single quotes
            "\u0093": '"', "\u0094": '"',   # Double quotes
            "\u0096": "-", "\u0097": "-",   # Dashes
            "\u00a0": " ",                  # Non-breaking space
            "\u200b": "",                   # Zero-width space
            "“": '"', "”": '"',             # Smart double quotes
            "‘": "'", "’": "'",             # Smart single quotes
            "—": "-", "–": "-",             # Em-dash and En-dash
            "…": "..."                     # Ellipsis
        }
        for old, new in winansi_replacements.items():
            text = text.replace(old, new)

        # NFKC Normalization (converts ligatures like fi -> fi, fullwidth chars, etc.)
        text = unicodedata.normalize("NFKC", text)
            
        # Strip remaining unprintable control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text

    def remove_page_numbers_and_footers(self, text: str) -> str:
        """Strip standalone page numbers and page footer patterns using Regex"""
        if not text:
            return ""
        
        lines = text.splitlines()
        cleaned_lines = []
        
        # Regex patterns for page numbers
        page_num_patterns = [
            r'^\s*page\s+\d+(\s+of\s+\d+)?\s*$',         # Page 1, Page 1 of 10
            r'^\s*-\s*\d+\s*-\s*$',                     # - 1 -
            r'^\s*\[\s*page\s*\d+\s*\]\s*$',            # [Page 1]
            r'^\s*\d+\s*/\s*\d+\s*$',                   # 1 / 10
            r'^\s*page\s*-\s*\d+\s*-\s*$',              # Page - 1 -
            r'^\s*\d+\s*$'                             # Standalone single line number
        ]
        combined_pattern = re.compile('|'.join(page_num_patterns), re.IGNORECASE)
        
        for line in lines:
            if combined_pattern.match(line.strip()):
                continue  # Skip standalone page number line
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    def remove_running_headers_footers(self, pages_text: List[str]) -> List[str]:
        """Detect and remove repetitive top/bottom running header and footer lines across pages"""
        if len(pages_text) <= 1:
            return pages_text
            
        # Collect candidate header (first non-empty line) and footer (last non-empty line)
        top_candidates = []
        bottom_candidates = []
        
        for p_text in pages_text:
            lines = [l.strip() for l in p_text.splitlines() if l.strip()]
            if lines:
                top_candidates.append(lines[0])
                bottom_candidates.append(lines[-1])
                
        # Count frequencies
        top_counts = Counter(top_candidates)
        bottom_counts = Counter(bottom_candidates)
        
        # Headers/footers appearing on >= 50% of multi-page documents are considered repetitive
        threshold = max(2, len(pages_text) * 0.5)
        repetitive_headers = {line for line, count in top_counts.items() if count >= threshold}
        repetitive_footers = {line for line, count in bottom_counts.items() if count >= threshold}
        
        cleaned_pages = []
        for p_text in pages_text:
            lines = p_text.splitlines()
            filtered_lines = []
            for l in lines:
                stripped = l.strip()
                if stripped in repetitive_headers or stripped in repetitive_footers:
                    continue
                filtered_lines.append(l)
            cleaned_pages.append("\n".join(filtered_lines))
            
        return cleaned_pages

    def normalize_whitespace(self, text: str) -> str:
        """Collapse multiple inline spaces/tabs to a single space and reduce 3+ newlines to max 2 newlines"""
        if not text:
            return ""
            
        # Collapse multiple horizontal spaces/tabs on each line
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
        text = "\n".join(lines)
        
        # Reduce 3 or more consecutive newlines to maximum 2 newlines (\n\n)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def clean_page_text(self, text: str) -> str:
        """Run complete single-page cleaning pipeline"""
        text = self.normalize_unicode(text)
        text = self.remove_page_numbers_and_footers(text)
        text = self.normalize_whitespace(text)
        return text

    def clean_document(self, file_id: str) -> CleanedDocumentResponse:
        """
        Main Orchestrator: Fetches parsed output (or parses document if needed),
        runs unicode, page-number, header/footer, and whitespace cleaning pipelines,
        saves artifact to ./storage/cleaned/<file_id>_cleaned.json, and updates status.
        """
        # Step 1: Ensure parsed output is available
        parsed_doc = parser_service.get_parsed_document(file_id)
        if not parsed_doc:
            parsed_doc = parser_service.parse_document(file_id)

        # Step 2: Extract text from all pages
        raw_pages_text = [p.text for p in parsed_doc.pages]

        # Step 3: Remove repetitive headers/footers across pages
        pages_without_headers = self.remove_running_headers_footers(raw_pages_text)

        # Step 4: Clean each page
        cleaned_pages: List[CleanedPage] = []
        for idx, (raw_page, p_text) in enumerate(zip(parsed_doc.pages, pages_without_headers)):
            cleaned_text = self.clean_page_text(p_text)
            cleaned_pages.append(CleanedPage(
                page_number=raw_page.page_number,
                raw_char_count=raw_page.char_count,
                cleaned_char_count=len(cleaned_text),
                cleaned_text=cleaned_text
            ))

        # Step 5: Assemble full cleaned text with page dividers
        full_cleaned = "\n\n".join([
            f"--- Page {p.page_number} ---\n{p.cleaned_text}"
            for p in cleaned_pages if p.cleaned_text
        ])

        cleaned_response = CleanedDocumentResponse(
            file_id=parsed_doc.file_id,
            original_filename=parsed_doc.original_filename,
            total_pages=parsed_doc.total_pages,
            full_cleaned_text=full_cleaned,
            pages=cleaned_pages,
            cleaned_at=datetime.now(timezone.utc).isoformat(),
            status="cleaned"
        )

        # Step 6: Persist JSON artifact
        json_path = self.cleaned_dir / f"{file_id}_cleaned.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(cleaned_response.model_dump_json(indent=2))

        # Also save raw text output for direct previewing
        txt_path = self.cleaned_dir / f"{file_id}_cleaned.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_cleaned)

        # Step 7: Update document metadata status
        metadata = metadata_service.get_metadata_by_id(file_id)
        if metadata:
            metadata.status = "cleaned"
            metadata_service.save_metadata(metadata)

        return cleaned_response

    def get_cleaned_document(self, file_id: str) -> Optional[CleanedDocumentResponse]:
        """Retrieve stored cleaned document response JSON if available"""
        json_path = self.cleaned_dir / f"{file_id}_cleaned.json"
        if not json_path.exists():
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CleanedDocumentResponse(**data)
        except Exception:
            return None

# Default singleton instance
cleaner_service = TextCleaner()
