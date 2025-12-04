# app/main.py

import os
import time
from math import ceil
from typing import List

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import Message, SearchResult
from .search import search_messages

UPSTREAM_URL = "https://november7-730026606190.europe-west1.run.app/messages"

MESSAGE_CACHE: List[Message] = []

app = FastAPI(title="Message Search Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "messages_cached": len(MESSAGE_CACHE)}


async def fetch_all_messages() -> List[Message]:
    messages = []
    limit = 200
    offset = 0

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        while True:
            url = f"{UPSTREAM_URL}?limit={limit}&offset={offset}"
            resp = await client.get(url)
            resp.raise_for_status()

            data = resp.json()
            items = data["items"]
            total = data["total"]

            messages.extend(items)

            if len(messages) >= total:
                break

            offset += limit

    return [Message.model_validate(m) for m in messages]


@app.on_event("startup")
async def load_data():
    global MESSAGE_CACHE
    print("Loading messages from upstream...")
    MESSAGE_CACHE = await fetch_all_messages()
    print(f"Loaded {len(MESSAGE_CACHE)} messages into cache.")


@app.get("/search", response_model=SearchResult)
async def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if not MESSAGE_CACHE:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    start_time = time.perf_counter()

    matched = search_messages(MESSAGE_CACHE, q)
    total = len(matched)
    total_pages = ceil(total / page_size) if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size

    if start >= total and total > 0:
        raise HTTPException(status_code=400, detail="Page out of range")

    page_items = matched[start:end]

    took_ms = (time.perf_counter() - start_time) * 1000

    return SearchResult(
        query=q,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        took_ms=round(took_ms, 2),
        results=page_items,
    )
