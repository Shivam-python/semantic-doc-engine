from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.query_engine import engine

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

class Citation(BaseModel):
    label: str
    id: Any
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Synchronous Q&A; returns answer + citations + confidence score.
    """
    try:
        result = await engine.query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
