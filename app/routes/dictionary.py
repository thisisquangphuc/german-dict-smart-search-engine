from fastapi import APIRouter, HTTPException
from app.services.pons_service import PonsService
from app.models import PonsResponse

router = APIRouter()
pons_service = PonsService()

@router.get("/api/dict/pons", response_model=PonsResponse)
async def get_word_definition(word: str):
    """
    Get word definition from PONS dictionary with caching.
    
    Args:
        word (str): The word to look up
        
    Returns:
        PonsResponse: The word definition and cache status
    """
    if not word:
        raise HTTPException(status_code=400, detail="Word parameter is required")
    
    result = await pons_service.get_definition(word)
    return result 