# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class BookBase(BaseModel):
    title: str
    author: str
    published_date: Optional[str] = None
    summary: Optional[str] = None
    genre: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    summary: Optional[str] = None
    genre: Optional[str] = None

class BookRead(BookBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TokenSchema(BaseModel):
    access_token: str
    token_type: str

class PaginatedBooks(BaseModel):
    data: List[BookRead]
    total_count: int
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
