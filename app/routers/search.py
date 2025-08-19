from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth import get_current_user
from ..rag_service import rag_service
from ..openai_service import openai_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # risks, controls, guidance, all
    limit: int = 10

@router.post("/similar-risks")
async def search_similar_risks(request: SearchRequest, user = Depends(get_current_user)):
    try:
        query_embedding = openai_service.get_embedding(request.query)
        results = rag_service.vector_db.search_similar_risks(query_embedding, request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similar-controls") 
async def search_similar_controls(request: SearchRequest, user = Depends(get_current_user)):
    try:
        query_embedding = openai_service.get_embedding(request.query)
        results = rag_service.vector_db.search_similar_controls(query_embedding, limit=request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/iso-guidance")
async def search_iso_guidance(request: SearchRequest, user = Depends(get_current_user)):
    try:
        query_embedding = openai_service.get_embedding(request.query)
        results = rag_service.vector_db.get_iso_guidance(query_embedding, request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comprehensive")
async def comprehensive_search(request: SearchRequest, user = Depends(get_current_user)):
    try:
        context = rag_service._get_general_query_context(
            openai_service.get_embedding(request.query),
            user["username"]
        )
        return {"context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))