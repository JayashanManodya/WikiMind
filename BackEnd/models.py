from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from BackEnd.database import Base

class DocumentModel(Base):
    __tablename__ = "documents"

    file_id = Column(String, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String, nullable=False)
    uploaded_at = Column(String, nullable=False)
    status = Column(String, default="stored", nullable=False)

    entities = relationship("EntityModel", back_populates="document", cascade="all, delete-orphan")
    definitions = relationship("DefinitionModel", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("FactModel", back_populates="document", cascade="all, delete-orphan")
    relationships_list = relationship("RelationshipModel", back_populates="document", cascade="all, delete-orphan")


class EntityModel(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("documents.file_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

    document = relationship("DocumentModel", back_populates="entities")


class DefinitionModel(Base):
    __tablename__ = "definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("documents.file_id", ondelete="CASCADE"), nullable=False, index=True)
    term = Column(String, nullable=False, index=True)
    definition = Column(Text, nullable=False)

    document = relationship("DocumentModel", back_populates="definitions")


class FactModel(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("documents.file_id", ondelete="CASCADE"), nullable=False, index=True)
    fact = Column(Text, nullable=False)
    confidence = Column(Float, default=0.95)
    source_section = Column(String, nullable=True)

    document = relationship("DocumentModel", back_populates="facts")


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("documents.file_id", ondelete="CASCADE"), nullable=False, index=True)
    source_entity = Column(String, nullable=False, index=True)
    relation = Column(String, nullable=False)
    target_entity = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    document = relationship("DocumentModel", back_populates="relationships_list")


class WikiPageModel(Base):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String, unique=True, nullable=False, index=True)
    filename = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    links_json = Column(Text, nullable=True)
    updated_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())
