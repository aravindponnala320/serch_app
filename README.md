# Aurora Search App

A FastAPI-based message search engine that fetches messages from an upstream API and provides fast search capabilities.

## Features

- Fetches and caches messages from upstream API on startup
- Full-text search across messages
- Paginated search results
- CORS-enabled REST API
- Health check endpoint

## Prerequisites

- Python 3.11+
- Docker (optional)

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r app/requirements.txt
```

## Running Locally

```bash
uvicorn app.main:app --reload --port 8080
```

The API will be available at `http://localhost:8080`

## Running with Docker

```bash
docker build -t aurora-search-app .
docker run -p 8080:8080 aurora-search-app
```

## API Endpoints

### Health Check
```
GET /health
```
Returns service status and number of cached messages.

### Search Messages
```
GET /search?q=<query>&page=<page>&page_size=<size>
```

**Parameters:**
- `q` (required): Search query string
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Results per page

**Response:**
```json
{
  "query": "search term",
  "page": 1,
  "page_size": 20,
  "total": 100,
  "total_pages": 5,
  "took_ms": 12.34,
  "results": [
    {
      "id": "msg-123",
      "user_id": "user-456",
      "user_name": "John Doe",
      "timestamp": "2025-12-03T20:00:00Z",
      "message": "Message content"
    }
  ]
}
```

## Project Structure

```
aurora_serch_app/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models
│   ├── search.py        # Search logic
│   ├── repository.py    # Data access layer
│   └── requirements.txt
├── Dockerfile
└── .env
```

## Configuration

The upstream API URL is configured in `main.py`:
```python
UPSTREAM_URL = "https://november7-730026606190.europe-west1.run.app/messages"
```

## Alternative Designs Considered

### Local database with full-text index (PostgreSQL / SQLite FTS5)

Save messages into a DB; add full-text index. Query DB on `/search`.

**Pros:**
- Better scaling when dataset grows
- SQL query capabilities (filters, sort by date, etc.)

**Cons:**
- More infra and complexity than needed for this assignment
- Good next step if messages become large (100k+ / millions)

### Dedicated search engine (Meilisearch / Elasticsearch / OpenSearch)

Ingest messages into a search engine. `/search` hits search engine instead of scanning.

**Pros:**
- Very powerful relevance, fuzziness, filters
- Designed for sub-10ms queries on huge datasets

**Cons:**
- Requires running extra infra
- Overkill for a small take-home, but realistic in production

## Performance Optimization Strategies

### Put everything in the same region

Deploy this search service close to the calling client and/or upstream GET /messages (e.g., same GCP region).

That reduces network RTT.

### Avoid network calls in the hot path

The current design already does this: /search never calls GET /messages.

All searching is done in memory.

### Optimize the search itself

For very large datasets:

- Build an inverted index (term → list of message IDs) at startup
- Lookup becomes O(k) in number of matching docs instead of scanning all documents
- Using a library (e.g., Whoosh, or SQLite FTS) would give you single-digit ms query times

### Runtime + server tuning

- Run with uvicorn + uvloop on a reasonably sized instance
- Keep connections warm (no cold starts)
- Avoid logging every request in hot paths

### Pre-filtering and limits

- Limit page_size (e.g., max 50–100)
- Only return necessary fields, minimize JSON size

Together, these changes make 30ms p95 very realistic for a moderate dataset.
