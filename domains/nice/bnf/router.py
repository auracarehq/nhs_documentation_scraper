"""Router for NICE British National Formulary (BNF) drug monographs."""

from __future__ import annotations

import asyncio

import db
from domains.models import ItemContent, ItemSummary, TaskResponse
from domains.nice.service import scrape_all, scrape_one
from fastapi import APIRouter, HTTPException
from tasks import create_task, get_active_scrape, register_async_task, set_active_scrape

DOMAIN = "nice:bnf"
LABEL = "NICE BNF"

router = APIRouter(prefix="/nice/bnf", tags=[LABEL])


@router.post(
    "/scrape",
    response_model=TaskResponse,
    summary=f"Scrape all {LABEL} drug monographs",
    description="Start a background task that scrapes every drug from the NICE BNF A-Z listing.",
)
async def scrape_all_bnf(force: bool = False) -> TaskResponse:
    """Enqueue a full NICE BNF scrape."""
    scrape_key = f"{DOMAIN}:all"
    existing = get_active_scrape(scrape_key)
    if existing:
        raise HTTPException(409, detail={"message": f"A scrape for {LABEL} is already running", "task_id": existing.task_id})
    task = create_task()
    set_active_scrape(scrape_key, task.task_id)
    async_task = asyncio.create_task(scrape_all(DOMAIN, task.task_id, scrape_key, force=force))
    register_async_task(task.task_id, async_task)
    return TaskResponse(task_id=task.task_id)


@router.post(
    "/scrape/{slug}",
    response_model=TaskResponse,
    summary="Scrape a single BNF drug",
    description="Start a background task that scrapes one NICE BNF drug monograph by slug.",
)
async def scrape_one_bnf(slug: str) -> TaskResponse:
    """Enqueue a single NICE BNF drug scrape."""
    scrape_key = f"{DOMAIN}:{slug}"
    existing = get_active_scrape(scrape_key)
    if existing:
        raise HTTPException(409, detail={"message": f"A scrape for {slug} is already running", "task_id": existing.task_id})
    task = create_task()
    set_active_scrape(scrape_key, task.task_id)
    async_task = asyncio.create_task(scrape_one(DOMAIN, slug, task.task_id, scrape_key))
    register_async_task(task.task_id, async_task)
    return TaskResponse(task_id=task.task_id)


@router.get(
    "/",
    response_model=list[ItemSummary],
    summary=f"List scraped {LABEL} drugs",
    description="Return slug and name for every previously scraped BNF drug monograph.",
)
async def list_bnf() -> list[ItemSummary]:
    """List all scraped NICE BNF drug monographs."""
    pool = db.get_pool()
    rows = await db.list_pages(pool, DOMAIN)
    return [ItemSummary(slug=r["slug"], name=r["name"]) for r in rows]


@router.get(
    "/{slug}",
    response_model=ItemContent,
    summary="Get a scraped BNF drug",
    description="Retrieve full markdown content and metadata for a single BNF drug monograph.",
)
async def get_bnf(slug: str) -> ItemContent:
    """Fetch one scraped NICE BNF drug monograph by slug."""
    pool = db.get_pool()
    row = await db.get_page(pool, DOMAIN, slug)
    if row is None:
        raise HTTPException(404, f"{slug} not found")
    return ItemContent(
        slug=row["slug"], name=row["name"], url=row["url"],
        page_last_reviewed=row["page_last_reviewed"],
        next_review_due=row["next_review_due"], markdown=row["markdown"],
    )


@router.delete("/{slug}", summary="Delete a scraped BNF drug")
async def delete_bnf(slug: str) -> dict:
    """Remove a scraped NICE BNF drug monograph from the database."""
    pool = db.get_pool()
    deleted = await db.delete_page(pool, DOMAIN, slug)
    if not deleted:
        raise HTTPException(404, f"{slug} not found")
    return {"deleted": slug}
