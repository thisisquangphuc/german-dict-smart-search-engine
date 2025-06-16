from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class PonsCache(SQLModel, table=True):
    __tablename__ = "pons_cache"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(unique=True, index=True)
    result: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    search_count: int = Field(default=1)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

class PonsResponse(BaseModel):
    word: str
    result: str
    is_cached: bool = False 