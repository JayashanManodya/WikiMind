import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from BackEnd.database import SessionLocal, init_db
from BackEnd.models import (
    DocumentModel,
    EntityModel,
    DefinitionModel,
    FactModel,
    RelationshipModel,
    WikiPageModel
)
from BackEnd.schemas import DocumentMetadata, KnowledgeExtractionResponse, WikiPageSummary

class DatabaseService:
    def __init__(self):
        init_db()

    def get_session(self) -> Session:
        return SessionLocal()

    # --- Document Metadata Persistence ---

    def save_document(self, metadata: DocumentMetadata) -> DocumentModel:
        """Persist or update document metadata in SQLite/PostgreSQL database"""
        session = self.get_session()
        try:
            doc = session.query(DocumentModel).filter(DocumentModel.file_id == metadata.file_id).first()
            if not doc:
                doc = DocumentModel(
                    file_id=metadata.file_id,
                    original_filename=metadata.original_filename,
                    stored_filename=metadata.stored_filename,
                    file_path=metadata.file_path,
                    content_type=metadata.content_type,
                    size_bytes=metadata.size_bytes,
                    sha256_hash=metadata.sha256_hash,
                    uploaded_at=metadata.uploaded_at,
                    status=metadata.status
                )
                session.add(doc)
            else:
                doc.status = metadata.status
                doc.original_filename = metadata.original_filename
                doc.file_path = metadata.file_path

            session.commit()
            session.refresh(doc)
            return doc
        finally:
            session.close()

    def get_document(self, file_id: str) -> Optional[DocumentModel]:
        session = self.get_session()
        try:
            return session.query(DocumentModel).filter(DocumentModel.file_id == file_id).first()
        finally:
            session.close()

    def get_all_documents(self) -> List[DocumentModel]:
        session = self.get_session()
        try:
            return session.query(DocumentModel).all()
        finally:
            session.close()

    # --- Knowledge Artifact Persistence ---

    def save_knowledge(self, knowledge: KnowledgeExtractionResponse):
        """Persist extracted entities, definitions, facts, and relationships into relational DB tables"""
        session = self.get_session()
        try:
            file_id = knowledge.file_id

            # Clear existing records for this document to allow re-extraction idempotency
            session.query(EntityModel).filter(EntityModel.file_id == file_id).delete()
            session.query(DefinitionModel).filter(DefinitionModel.file_id == file_id).delete()
            session.query(FactModel).filter(FactModel.file_id == file_id).delete()
            session.query(RelationshipModel).filter(RelationshipModel.file_id == file_id).delete()

            # Insert Entities
            for e in knowledge.entities:
                session.add(EntityModel(
                    file_id=file_id,
                    name=e.name,
                    type=e.type,
                    description=e.description
                ))

            # Insert Definitions
            for d in knowledge.definitions:
                session.add(DefinitionModel(
                    file_id=file_id,
                    term=d.term,
                    definition=d.definition
                ))

            # Insert Facts
            for f in knowledge.facts:
                session.add(FactModel(
                    file_id=file_id,
                    fact=f.fact,
                    confidence=f.confidence,
                    source_section=f.source_section
                ))

            # Insert Relationships
            for r in knowledge.relationships:
                session.add(RelationshipModel(
                    file_id=file_id,
                    source_entity=r.source_entity,
                    relation=r.relation,
                    target_entity=r.target_entity,
                    description=r.description
                ))

            # Update Document status
            doc = session.query(DocumentModel).filter(DocumentModel.file_id == file_id).first()
            if doc:
                doc.status = "extracted"

            session.commit()
        finally:
            session.close()

    # --- Wiki Page Persistence ---

    def save_wiki_page(
        self,
        entity_name: str,
        filename: str,
        entity_type: str,
        filepath: str,
        content: str,
        links: List[str],
        updated_at: str
    ) -> WikiPageModel:
        """Persist or update Wiki Page record in DB"""
        session = self.get_session()
        try:
            links_str = json.dumps(links)
            page = session.query(WikiPageModel).filter(WikiPageModel.entity_name == entity_name).first()
            if not page:
                page = WikiPageModel(
                    entity_name=entity_name,
                    filename=filename,
                    entity_type=entity_type,
                    filepath=filepath,
                    content=content,
                    links_json=links_str,
                    updated_at=updated_at
                )
                session.add(page)
            else:
                page.filename = filename
                page.entity_type = entity_type
                page.filepath = filepath
                page.content = content
                page.links_json = links_str
                page.updated_at = updated_at

            session.commit()
            session.refresh(page)
            return page
        finally:
            session.close()

    def get_wiki_page_by_name(self, entity_name: str) -> Optional[WikiPageModel]:
        session = self.get_session()
        try:
            return session.query(WikiPageModel).filter(WikiPageModel.entity_name.ilike(entity_name)).first()
        finally:
            session.close()

    def get_all_wiki_pages(self) -> List[WikiPageModel]:
        session = self.get_session()
        try:
            return session.query(WikiPageModel).order_by(WikiPageModel.entity_name.asc()).all()
        finally:
            session.close()

    # --- Query & Stats Helpers ---

    def get_database_stats(self) -> Dict[str, int]:
        session = self.get_session()
        try:
            return {
                "total_documents": session.query(DocumentModel).count(),
                "total_entities": session.query(EntityModel).count(),
                "total_definitions": session.query(DefinitionModel).count(),
                "total_facts": session.query(FactModel).count(),
                "total_relationships": session.query(RelationshipModel).count(),
                "total_wiki_pages": session.query(WikiPageModel).count()
            }
        finally:
            session.close()

# Default singleton instance
db_service = DatabaseService()
