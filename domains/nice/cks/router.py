"""Router for NICE Clinical Knowledge Summaries (CKS)."""

from __future__ import annotations

import asyncio

import db
from domains.models import ItemContent, ItemSummary, TaskResponse
from domains.nice.service import scrape_all, scrape_one
from fastapi import APIRouter, HTTPException
from tasks import create_task, get_active_scrape, register_async_task, set_active_scrape

DOMAIN = "nice:cks"
LABEL = "NICE CKS"

router = APIRouter(prefix="/nice/cks", tags=[LABEL])


@router.post(
    "/scrape",
    response_model=TaskResponse,
    summary=f"Scrape all {LABEL} topics",
    description="Start a background task that scrapes every topic from the NICE CKS A-Z listing.",
)
async def scrape_all_cks(force: bool = False) -> TaskResponse:
    """Enqueue a full NICE CKS scrape."""
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
    summary="Scrape a single CKS topic",
    description="Start a background task that scrapes one NICE CKS topic by slug.",
)
async def scrape_one_cks(slug: str) -> TaskResponse:
    """Enqueue a single NICE CKS topic scrape."""
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
    summary=f"List scraped {LABEL} topics",
    description="Return slug and name for every previously scraped CKS topic.",
)
async def list_cks() -> list[ItemSummary]:
    """List all scraped NICE CKS topics."""
    pool = db.get_pool()
    rows = await db.list_pages(pool, DOMAIN)
    return [ItemSummary(slug=r["slug"], name=r["name"]) for r in rows]


@router.get(
    "/{slug}",
    response_model=ItemContent,
    summary="Get a scraped CKS topic",
    description="Retrieve full markdown content and metadata for a single CKS topic.",
)
async def get_cks(slug: str) -> ItemContent:
    """Fetch one scraped NICE CKS topic by slug."""
    pool = db.get_pool()
    row = await db.get_page(pool, DOMAIN, slug)
    if row is None:
        raise HTTPException(404, f"{slug} not found")
    return ItemContent(
        slug=row["slug"], name=row["name"], url=row["url"],
        page_last_reviewed=row["page_last_reviewed"],
        next_review_due=row["next_review_due"], markdown=row["markdown"],
    )


@router.delete("/{slug}", summary="Delete a scraped CKS topic")
async def delete_cks(slug: str) -> dict:
    """Remove a scraped NICE CKS topic from the database."""
    pool = db.get_pool()
    deleted = await db.delete_page(pool, DOMAIN, slug)
    if not deleted:
        raise HTTPException(404, f"{slug} not found")
    return {"deleted": slug}
