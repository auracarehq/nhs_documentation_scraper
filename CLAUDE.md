# CLAUDE.md

Python + Docker codebase.

## Run & Test

```bash
docker compose up --build                          # API + Postgres
docker compose --profile tools run --rm test       # all tests (style + unit)
```

## Architecture

- `main.py`: FastAPI app, lifespan, top-level routes (Swagger at `/docs`)
- `config.py`: scraper rate-limiting config
- `db.py`: SQLAlchemy async ORM; `scraped_pages` table (NHS/NICE/MHRA content) + `snomed_concepts` table
- `tasks.py`: in-memory task store for background scrapes
- `domains/models.py`: shared response models (TaskResponse, SearchResult)
- `scraper/`: HTTP client, NHS A-Z index parser, page parser, markdown converter

### NHS Health A-Z (`domains/nhs/`)
- `config.py`: base URL + domain registry (conditions, symptoms, medicines, treatments)
- `models.py`: ItemSummary, ItemContent (reused by NICE and MHRA routers)
- `service.py`: scrape orchestration (scrape_all, scrape_one, update_stale)
- `{conditions,symptoms,medicines,treatments}/router.py`: per-domain routers

### NICE (`domains/nice/`)
- `config.py`: base URLs + domain registry for CKS, BNF, BNFc
- `scraper.py`: NICE-specific index page parser (different link structure to NHS A-Z)
- `service.py`: scrape orchestration — reuses `scraper.page.scrape_page` for content
- `{cks,bnf,bnfc}/router.py`: per-domain routers
- Routes: `/nice/cks/`, `/nice/bnf/`, `/nice/bnfc/`

### MHRA (`domains/mhra/`)
- `config.py`: GOV.UK Content API endpoints
- `client.py`: GOV.UK search API + Content API (JSON, not HTML scraping)
- `service.py`: paginated fetch, HTML-body → markdown, upsert to DB
- `safety_updates/router.py`: CRUD + scrape endpoints
- Route: `/mhra/drug-safety-updates/`

### SNOMED CT (`domains/snomed/`)
- `config.py`: public IHTSDO Snowstorm API base URL + UK branch
- `models.py`: ConceptSummary, ConceptDetail, ConceptSearchResult
- `client.py`: Snowstorm REST API calls (search, get concept)
- `service.py`: search (live API), fetch_and_cache, get_or_fetch
- `router.py`: search, list cached, get/cache/delete concept
- Route: `/snomed/`
- Storage: `snomed_concepts` table (separate from `scraped_pages`)

## Conventions

- Keep `scraper/` independent — no imports from `domains`, `tasks`, or `main`.
- `models.py` and `config.py` files inside `domains/` stay dependency-free (no scraper/db/tasks/main).
- Domain-specific scrapers/clients live inside their domain package, not in `scraper/`.
- Postgres is the system of record — no filesystem storage.
- Style tests enforce limits automatically.
