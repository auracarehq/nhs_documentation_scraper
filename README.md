# Clinical Knowledge Scraper

A FastAPI service that scrapes clinical guidance sources and stores content in PostgreSQL as markdown with YAML frontmatter. Built for use as a knowledge backend for clinical applications.

## Sources

| Source | Route prefix | Method | Content |
|---|---|---|---|
| [NHS Health A-Z](https://www.nhs.uk) | `/conditions/` `/symptoms/` `/medicines/` `/treatments/` | HTML scrape | Conditions, symptoms, medicines, treatments |
| [NICE CKS](https://cks.nice.org.uk) | `/nice/cks/` | HTML scrape | Clinical Knowledge Summaries (380+ topics) |
| [NICE BNF](https://bnf.nice.org.uk) | `/nice/bnf/` | HTML scrape | British National Formulary drug monographs |
| [NICE BNFc](https://bnfc.nice.org.uk) | `/nice/bnfc/` | HTML scrape | BNF for Children drug monographs |
| [MHRA Drug Safety Updates](https://www.gov.uk/drug-safety-update) | `/mhra/drug-safety-updates/` | GOV.UK Content API (JSON) | Drug safety alerts |
| [SNOMED CT UK Edition](https://browser.ihtsdotools.org) | `/snomed/` | Snowstorm REST API | Concept search + local cache |

## Quick Start

```bash
make up
```

API at **http://localhost:8888** — Swagger docs at **http://localhost:8888/docs**.

## Makefile

| Target | Description |
|---|---|
| `make up` | Build and start API + Postgres |
| `make down` | Stop all services |
| `make build` | Build Docker images only |
| `make test` | Run all tests (style + unit) |
| `make logs` | Tail service logs |
| `make clean` | Stop services and remove volumes |

## API

All scrapers run as background tasks. The workflow is always:

1. `POST /{domain}/scrape` → `{"task_id": "a1b2c3d4e5f6"}`
2. `GET /tasks/{task_id}` → poll until `status` is `completed` or `failed`
3. `GET /{domain}/` → list scraped items; `GET /{domain}/{slug}` → full content

### Scrape a whole domain

```bash
# NHS conditions
curl -X POST http://localhost:8888/conditions/scrape

# NICE CKS topics
curl -X POST http://localhost:8888/nice/cks/scrape

# NICE BNF drugs
curl -X POST http://localhost:8888/nice/bnf/scrape

# MHRA Drug Safety Updates (fetches from GOV.UK JSON API, no HTML scraping)
curl -X POST http://localhost:8888/mhra/drug-safety-updates/scrape
```

Items already in the database are skipped. Force a full re-scrape:

```bash
curl -X POST "http://localhost:8888/conditions/scrape?force=true"
```

### Scrape a single item

```bash
curl -X POST http://localhost:8888/conditions/scrape/acne
curl -X POST http://localhost:8888/nice/cks/scrape/acne
curl -X POST http://localhost:8888/nice/bnf/scrape/metformin-hydrochloride
curl -X POST "http://localhost:8888/mhra/drug-safety-updates/scrape/some-article-slug"
```

Duplicate requests return `409 Conflict` if the same domain or slug is already running.

### Update stale pages (NHS only)

Re-scrape items whose `next_review_due` date has passed:

```bash
curl -X POST http://localhost:8888/conditions/update
```

### Poll task progress

```bash
curl http://localhost:8888/tasks/{task_id}
# {"task_id": "...", "status": "running", "done": 42, "total": 380, "message": "..."}
```

Status: `pending` → `running` → `completed` / `failed` / `cancelled`

### Cancel a running task

```bash
curl -X POST http://localhost:8888/tasks/{task_id}/cancel
```

### Browse scraped content

```bash
# List all items in a domain
curl http://localhost:8888/nice/cks/
curl http://localhost:8888/nice/bnf/
curl http://localhost:8888/mhra/drug-safety-updates/

# Get full markdown + metadata for one item
curl http://localhost:8888/nice/cks/acne
curl http://localhost:8888/nice/bnf/metformin-hydrochloride

# Delete an item
curl -X DELETE http://localhost:8888/nice/cks/acne
```

### Search across all domains

```bash
curl "http://localhost:8888/search?q=metformin"
# Returns matches from all scraped sources (NHS + NICE + MHRA)
```

### SNOMED CT

SNOMED is different: it's a live API proxy with an optional local cache, not a bulk scrape.

```bash
# Search by clinical term (always hits the Snowstorm API)
curl "http://localhost:8888/snomed/concepts?q=diabetes+mellitus"
curl "http://localhost:8888/snomed/concepts?q=metformin&limit=10"

# Get a concept by ID — returned from cache if present, fetched and cached otherwise
curl http://localhost:8888/snomed/concepts/73211009

# Force-refresh a specific concept in the cache
curl -X POST http://localhost:8888/snomed/concepts/73211009/cache

# List all locally cached concepts
curl http://localhost:8888/snomed/cached

# Remove a concept from the cache
curl -X DELETE http://localhost:8888/snomed/concepts/73211009
```

Search returns `concept_id`, `preferred_term`, `fsn` (fully specified name), and `active`. The hierarchy tag (`disorder`, `procedure`, `substance`, etc.) is extracted from the FSN and stored on cached concepts.

## Rate Limiting

All outbound HTTP requests — NHS, NICE, MHRA, and SNOMED — go through a single shared client (`scraper/client.py`) that enforces:

- **`MAX_CONCURRENT = 3`** concurrent requests (semaphore)
- **`REQUEST_DELAY = 0.5s`** pause after each request

Adjust both values in `config.py`. The SNOMED Snowstorm instance used is the public IHTSDO browser API; the shared rate limiter keeps usage within reasonable bounds.

## Project Structure

```
├── main.py                               # FastAPI app, lifespan, search + task endpoints
├── config.py                             # Shared rate-limiting config (MAX_CONCURRENT, REQUEST_DELAY)
├── db.py                                 # SQLAlchemy async ORM; scraped_pages + snomed_concepts tables
├── tasks.py                              # In-memory background task store
│
├── scraper/                              # Source-independent HTTP + parsing layer
│   ├── client.py                         # Rate-limited httpx client (shared by all sources)
│   ├── index.py                          # NHS A-Z index page parser
│   ├── page.py                           # Detail page + sub-tab parser (reused by NICE)
│   └── markdown.py                       # HTML → markdown + YAML frontmatter
│
├── domains/
│   ├── models.py                         # Shared models: ItemSummary, ItemContent, TaskResponse, SearchResult
│   │
│   ├── nhs/                              # NHS Health A-Z
│   │   ├── config.py                     # Base URL + domain registry
│   │   ├── service.py                    # scrape_all, scrape_one, update_stale
│   │   ├── conditions/router.py
│   │   ├── symptoms/router.py
│   │   ├── medicines/router.py
│   │   └── treatments/router.py
│   │
│   ├── nice/                             # NICE (CKS, BNF, BNFc)
│   │   ├── config.py                     # Base URLs + domain registry
│   │   ├── scraper.py                    # NICE-specific index parser (different link structure to NHS)
│   │   ├── service.py                    # scrape_all, scrape_one (reuses scraper.page for content)
│   │   ├── cks/router.py
│   │   ├── bnf/router.py
│   │   └── bnfc/router.py
│   │
│   ├── mhra/                             # MHRA Drug Safety Updates
│   │   ├── config.py                     # GOV.UK API endpoints
│   │   ├── client.py                     # GOV.UK search + Content API (JSON)
│   │   ├── service.py                    # Paginated fetch, HTML body → markdown
│   │   └── safety_updates/router.py
│   │
│   └── snomed/                           # SNOMED CT
│       ├── config.py                     # Snowstorm base URL + UK branch
│       ├── models.py                     # ConceptSummary, ConceptDetail, ConceptSearchResult
│       ├── client.py                     # Snowstorm REST API calls
│       ├── service.py                    # search (live), fetch_and_cache, get_or_fetch
│       └── router.py
│
├── tests/                                # Unit tests
│   └── style/                            # AST-based style tests (complexity, architecture, security, dead code)
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │               FastAPI (main.py)             │
                    └───────────────────┬─────────────────────────┘
                                        │
          ┌─────────────────────────────┼──────────────────────────┐
          │                             │                          │
    ┌─────▼──────┐              ┌───────▼──────┐           ┌──────▼──────┐
    │  NHS/NICE  │              │     MHRA     │           │   SNOMED    │
    │  service   │              │   service    │           │   service   │
    └─────┬──────┘              └──────┬───────┘           └──────┬──────┘
          │                            │                          │
    ┌─────▼──────┐              ┌──────▼───────┐           ┌──────▼──────┐
    │  scraper/  │              │ mhra/client  │           │snomed/client│
    │ (page, md) │              │ (GOV.UK API) │           │ (Snowstorm) │
    └─────┬──────┘              └──────┬───────┘           └──────┬──────┘
          │                            │                          │
          └────────────────────────────┼──────────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │ scraper/client  │
                              │ (rate-limited   │
                              │  httpx)         │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │   PostgreSQL    │
                              │ scraped_pages   │
                              │ snomed_concepts │
                              └─────────────────┘
```

**Layer rules (enforced by style tests):**
- `scraper/` is source-independent — no imports from `domains`, `tasks`, or `main`
- `domains/models.py` and `domains/*/config.py` and `domains/snomed/models.py` are dependency-free
- Domain-specific parsing logic (NICE index, MHRA JSON, SNOMED API) lives inside the domain package, not in `scraper/`

## Running Tests

```bash
make test
```

Style tests enforce complexity limits (function length, nesting depth, cyclomatic complexity), architecture layer boundaries, no dead private code, no security anti-patterns, and public docstring coverage — all automatically via AST analysis.

## License

[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)
