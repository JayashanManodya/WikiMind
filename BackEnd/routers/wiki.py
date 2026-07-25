from fastapi import APIRouter, HTTPException, status
from BackEnd.schemas import (
    WikiGenerationResponse,
    WikiIndexResponse,
    WikiPageResponse,
    ErrorDetail
)
from BackEnd.services.wiki_service import wiki_service

router = APIRouter(tags=["Wiki Generation Engine"])

@router.post(
    "/documents/{file_id}/generate-wiki",
    response_model=WikiGenerationResponse,
    summary="Generate Wiki Pages for Document",
    description="Transforms extracted document knowledge into structured Wikipedia-style markdown pages with internal wiki links.",
    responses={
        404: {"model": ErrorDetail, "description": "Document knowledge not found"},
        500: {"model": ErrorDetail, "description": "Wiki generation error"}
    }
)
def generate_wiki(file_id: str):
    """Trigger Wiki Markdown Page Generation for document file_id"""
    return wiki_service.generate_wiki_for_document(file_id)

@router.get(
    "/wiki/index",
    response_model=WikiIndexResponse,
    summary="Get Global Wiki Index",
    description="Retrieves catalog of all generated wiki topic pages in the knowledge base.",
)
def get_wiki_index():
    """Retrieve global Wiki index and list of available topic pages"""
    return wiki_service.get_wiki_index()

@router.get(
    "/wiki/page/{entity_name}",
    response_model=WikiPageResponse,
    summary="Get Specific Wiki Page",
    description="Retrieves full Markdown content, entity type, and connection links for a specific topic page.",
    responses={
        404: {"model": ErrorDetail, "description": "Wiki page not found"}
    }
)
def get_wiki_page(entity_name: str):
    """Retrieve Markdown Wiki page details by entity name or filename"""
    page = wiki_service.get_wiki_page(entity_name)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wiki page for entity '{entity_name}' not found."
        )
    return page
