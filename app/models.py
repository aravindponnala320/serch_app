# app/models.py
from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    id: str
    user_id: str
    user_name: str
    timestamp: str
    message: str


class SearchResult(BaseModel):
    query: str
    page: int
    page_size: int
    total: int
    total_pages: int
    took_ms: float
    results: List[Message]
