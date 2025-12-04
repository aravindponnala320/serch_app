# app/search.py
from typing import List
from .models import Message

def matches_query(msg: Message, query: str) -> bool:
    q = query.casefold()

    # Search in: message text + user_name
    haystack = f"{msg.message} {msg.user_name}".casefold()

    return q in haystack


def search_messages(messages: List[Message], query: str) -> List[Message]:
    q = query.strip()
    if not q:
        return []

    return [m for m in messages if matches_query(m, q)]
