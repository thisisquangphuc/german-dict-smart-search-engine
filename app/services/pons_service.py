import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx
from dotenv import load_dotenv
from sqlmodel import select
from app.models import PonsCache, PonsResponse
from app.database import get_session

load_dotenv()

PONS_API_KEY = os.getenv("PONS_API_KEY")
PONS_API_URL = "https://api.pons.com/v1/dictionary"

class PonsService:
    def __init__(self):
        if not PONS_API_KEY:
            raise ValueError("PONS_API_KEY not found in environment variables")
        
        self.headers = {
            "X-Secret": PONS_API_KEY
        }

    def _parse_pons_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse PONS API response into the format expected by the frontend."""
        try:
            data = json.loads(response_text)
            translations = []
            
            if not isinstance(data, list):
                return translations
                
            for entry in data:
                if "hits" not in entry:
                    continue
                    
                for hit in entry["hits"]:
                    if "roms" not in hit:
                        continue
                        
                    for rom in hit["roms"]:
                        if "arabs" not in rom:
                            continue
                            
                        for arab in rom["arabs"]:
                            if "translations" not in arab:
                                continue
                                
                            for translation in arab["translations"]:
                                source = translation.get("source", "")
                                target = translation.get("target", "")
                                
                                if source and target:
                                    translations.append({
                                        "source": source,
                                        "target": target,
                                        "sourceHtml": f"<span>{source}</span>",
                                        "targetHtml": f"<span>{target}</span>"
                                    })
            
            return translations
        except Exception as e:
            print(f"Error parsing PONS response: {e}")
            return []

    async def get_definition(self, word: str) -> PonsResponse:
        """Get word definition from PONS API with caching."""
        async with httpx.AsyncClient() as client:
            # First check cache
            cached_result = await self._get_from_cache(word)
            if cached_result:
                translations = self._parse_pons_response(cached_result.result)
                return PonsResponse(
                    word=word,
                    result=json.dumps({"translations": translations}),
                    is_cached=True
                )

            # If not in cache, call API
            try:
                response = await client.get(
                    f"{PONS_API_URL}?q={word}&l=deen",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    # Cache successful response
                    await self._save_to_cache(word, response.text)
                    translations = self._parse_pons_response(response.text)
                    return PonsResponse(
                        word=word,
                        result=json.dumps({"translations": translations}),
                        is_cached=False
                    )
                elif response.status_code == 429:
                    # If quota exceeded, try to get from cache again
                    cached_result = await self._get_from_cache(word)
                    if cached_result:
                        translations = self._parse_pons_response(cached_result.result)
                        return PonsResponse(
                            word=word,
                            result=json.dumps({"translations": translations}),
                            is_cached=True
                        )
                    return PonsResponse(
                        word=word,
                        result=json.dumps({"translations": [], "error": "API quota reached, no cached result available"}),
                        is_cached=False
                    )
                else:
                    return PonsResponse(
                        word=word,
                        result=json.dumps({"translations": [], "error": f"API error: {response.status_code}"}),
                        is_cached=False
                    )
            except Exception as e:
                return PonsResponse(
                    word=word,
                    result=json.dumps({"translations": [], "error": str(e)}),
                    is_cached=False
                )

    async def _get_from_cache(self, word: str) -> Optional[PonsCache]:
        """Get word definition from cache and update access statistics."""
        async with get_session() as session:
            statement = select(PonsCache).where(PonsCache.word == word)
            result = await session.execute(statement)
            cached_result = result.scalar_one_or_none()
            
            if cached_result:
                # Update access statistics
                cached_result.search_count += 1
                cached_result.last_accessed = datetime.utcnow()
                session.add(cached_result)
                await session.commit()
                return cached_result
            return None

    async def _save_to_cache(self, word: str, result: str) -> None:
        """Save word definition to cache."""
        async with get_session() as session:
            cache_entry = PonsCache(
                word=word,
                result=result,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            session.add(cache_entry)
            await session.commit() 