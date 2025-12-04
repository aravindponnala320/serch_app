# app/repository.py
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from math import ceil
from .models import Message


async def search_messages(
    db: AsyncSession,
    query: str,
    page: int,
    page_size: int,
) -> Tuple[List[Message], int, int]:
    """
    Use Postgres FTS:
      WHERE search_vector @@ plainto_tsquery('english', :q)
    Ranked by ts_rank.
    """

    # basic safety
    q = query.strip()
    if not q:
        return [], 0, 1

    offset = (page - 1) * page_size

    # total count (for pagination)
    count_stmt = text(
        """
        SELECT COUNT(*) AS count
        FROM messages
        WHERE search_vector @@ plainto_tsquery('english', :q)
        """
    ).bindparams(q=q)

    result = await db.execute(count_stmt)
    total = result.scalar_one()
    if total == 0:
        return [], 0, 1

    total_pages = max(1, ceil(total / page_size))

    # actual search with ranking + pagination
    search_stmt = text(
        """
        SELECT id::text,
               user_id::text,
               user_name,
               timestamp,
               message
        FROM messages
        WHERE search_vector @@ plainto_tsquery('english', :q)
        ORDER BY ts_rank(search_vector, plainto_tsquery('english', :q)) DESC,
                 timestamp DESC
        LIMIT :limit OFFSET :offset
        """
    ).bindparams(q=q, limit=page_size, offset=offset)

    rows = (await db.execute(search_stmt)).all()

    messages: List[Message] = [
        Message(
            id=row.id,
            user_id=row.user_id,
            user_name=row.user_name,
            timestamp=row.timestamp.isoformat() if hasattr(row.timestamp, "isoformat") else str(row.timestamp),
            message=row.message,
        )
        for row in rows
    ]

    return messages, total, total_pages
