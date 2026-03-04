# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

Everything runs through Docker. Do not install dependencies locally.

```bash
# Start the app (port 8000, Swagger at /docs)
docker compose up --build -d

# Run tests
docker compose run --rm app uv run pytest -v

# Run a single test
docker compose run --rm app uv run pytest tests/test_api.py::test_list_with_items -v

# Rebuild after code changes
docker compose up --build -d
```

The Dockerfile uses `uv` (Astral) for dependency management. Dependencies are in `pyproject.toml` — there is no `requirements.txt`. Pytest is configured with `asyncio_mode = "strict"`.

## Architecture

**Router factory pattern**: `domains/router.py:create_domain_router()` generates all endpoints for each domain. There are no per-domain router files — all four domains (conditions, symptoms, medicines, treatments) share the same factory. Adding a new domain means adding an entry to `config.DOMAINS` and mounting it in `main.py`.

**Scraper pipeline**: `scraper/index.py` parses A-Z listing pages → `scraper/page.py` fetches detail pages (handling multi-tab pages like Overview/Causes/Treatment) → `scraper/markdown.py` converts to markdown with YAML frontmatter → saves to `data/{domain}/{slug}.md`.

**Background tasks**: Scrape endpoints use `asyncio.create_task()` with an in-memory task store (`tasks.py`). Three module-level dicts track task status (`_store`), async handles for cancellation (`_async_tasks`), and active scrape keys for deduplication (`_active_scrapes`). Tasks are ephemeral — lost on restart.

**Filesystem as database**: All scraped content lives in `data/{domain}/{slug}.md` files with YAML frontmatter containing `name`, `url`, `page_last_reviewed`, `next_review_due`. List/get/delete endpoints read directly from disk.

**Rate limiting**: A shared `asyncio.Semaphore(3)` in `scraper/client.py` with 0.5s sleep between requests. The HTTP client is a module-level singleton initialized via FastAPI lifespan.

## Key Conventions

- `from __future__ import annotations` in all modules
- Dataclasses for internal data (`PageData`, `Section`, `IndexEntry`, `TaskStatus`); Pydantic `BaseModel` only for API responses
- Tests mock all HTTP calls via `AsyncMock` patches on `scraper.client.fetch` — no real network requests
- `tests/conftest.py:tmp_data_dir` fixture monkeypatches `config.DATA_DIR` and all domain data dirs to use `tmp_path`
- NHS review dates come as `"03 January 2023"` strings — `_parse_review_date()` in `router.py` handles parsing with fallbacks

## Scrape Deduplication

Active scrapes are keyed as `{domain}:all`, `{domain}:{slug}`, or `{domain}:update`. Duplicate requests return 409 with the existing task_id. Keys are cleared in `finally` blocks when tasks complete/fail/cancel.
