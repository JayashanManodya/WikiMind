import json
import os
from pathlib import Path
from typing import List, Optional
from threading import Lock
from BackEnd.schemas import DocumentMetadata

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class MetadataService:
    def __init__(self, metadata_dir: str = "./storage/metadata"):
        if isinstance(metadata_dir, str) and metadata_dir.startswith("./"):
            self.metadata_dir = (PROJECT_ROOT / metadata_dir[2:]).resolve()
        else:
            self.metadata_dir = Path(metadata_dir).resolve()
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.metadata_dir / "documents_metadata.json"
        self._lock = Lock()
        self._init_file()

    def _init_file(self):
        """Ensure metadata JSON file exists"""
        with self._lock:
            if not self.file_path.exists():
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)

    def _read_records(self) -> List[dict]:
        """Read raw dictionary records from JSON file"""
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _write_records(self, records: List[dict]):
        """Write raw dictionary records to JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def save_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Save a new metadata record or update an existing record by file_id"""
        with self._lock:
            records = self._read_records()
            record_dict = metadata.model_dump()
            
            # Check if record already exists
            existing_idx = next((i for i, r in enumerate(records) if r.get("file_id") == metadata.file_id), None)
            if existing_idx is not None:
                records[existing_idx] = record_dict
            else:
                records.append(record_dict)
                
            self._write_records(records)
            return metadata

    def get_all_metadata(self) -> List[DocumentMetadata]:
        """Retrieve all document metadata records"""
        with self._lock:
            records = self._read_records()
            return [DocumentMetadata(**r) for r in records]

    def get_metadata_by_id(self, file_id: str) -> Optional[DocumentMetadata]:
        """Retrieve document metadata by file_id"""
        with self._lock:
            records = self._read_records()
            record = next((r for r in records if r.get("file_id") == file_id), None)
            return DocumentMetadata(**record) if record else None

# Default singleton instance
metadata_service = MetadataService()
