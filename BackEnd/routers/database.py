from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from BackEnd.services.db_service import db_service

router = APIRouter(prefix="/database", tags=["Knowledge Storage Engine"])

@router.get(
    "/stats",
    summary="Get Relational Database Statistics",
    description="Retrieves record counts across documents, entities, definitions, facts, relationships, and wiki pages in the database.",
)
def get_database_stats() -> Dict[str, int]:
    """Retrieve overview statistics for all database tables"""
    return db_service.get_database_stats()

@router.get(
    "/entities",
    summary="List Extracted Entities from Database",
    description="Query extracted domain entities stored in the relational database.",
)
def get_database_entities(
    file_id: Optional[str] = Query(None, description="Filter entities by Document file_id")
) -> List[Dict[str, Any]]:
    """Retrieve entities persisted in the database"""
    session = db_service.get_session()
    try:
        from BackEnd.models import EntityModel
        query = session.query(EntityModel)
        if file_id:
            query = query.filter(EntityModel.file_id == file_id)
        entities = query.all()
        return [
            {
                "id": e.id,
                "file_id": e.file_id,
                "name": e.name,
                "type": e.type,
                "description": e.description,
                "created_at": e.created_at
            }
            for e in entities
        ]
    finally:
        session.close()

@router.get(
    "/relationships",
    summary="List Extracted Relationships from Database",
    description="Query directional graph relationships stored in the relational database.",
)
def get_database_relationships(
    file_id: Optional[str] = Query(None, description="Filter relationships by Document file_id")
) -> List[Dict[str, Any]]:
    """Retrieve relationships persisted in the database"""
    session = db_service.get_session()
    try:
        from BackEnd.models import RelationshipModel
        query = session.query(RelationshipModel)
        if file_id:
            query = query.filter(RelationshipModel.file_id == file_id)
        rels = query.all()
        return [
            {
                "id": r.id,
                "file_id": r.file_id,
                "source_entity": r.source_entity,
                "relation": r.relation,
                "target_entity": r.target_entity,
                "description": r.description
            }
            for r in rels
        ]
    finally:
        session.close()
