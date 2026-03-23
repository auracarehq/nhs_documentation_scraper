"""Router for MHRA Drug Safety Updates."""

from __future__ import annotations

import asyncio

import db
from domains.models import TaskResponse
from domains.mhra.config import DSU_DOMAIN
from domains.mhra.service import scrape_all_dsu, scrape_one_dsu
from domains.nhs.models import ItemContent, ItemSummary
from fastapi import APIRouter, HTTPException
from tasks import create_task, get_active_scrape, register_async_task, set_active_scrape

LABEL = "MHRA Drug Safety Updates"

router = APIRouter(prefix="/mhra/drug-safety-updates", tags=[LABEL])


@router.post(
    "/scrape",
    response_model=TaskResponse,
    summary="Scrape all MHRA Drug Safety Updates",
    description=(
        "Start a background task that fetches all Drug Safety Update articles from "
        "the GOV.UK Content API and stores them as markdown."
    ),
)
async def scrape_all_safety_updates(force: bool = False) -> TaskResponse:
    """Enqueue a full MHRA Drug Safety Updates scrape."""
    scrape_key = f"{DSU_DOMAIN}:all"
    existing = get_active_scrape(scrape_key)
    if existing:
        raise HTTPException(409, detail={"message": f"A scrape for {LABEL} is already running", "task_id": existing.task_id})
    task = create_task()
    set_active_scrape(scrape_key, task.task_id)
    async_task = asyncio.create_task(scrape_all_dsu(task.task_id, scrape_key, force=force))
    register_async_task(task.task_id, async_task)
    return TaskResponse(task_id=task.task_id)


@router.post(
    "/scrape/{slug}",
    response_model=TaskResponse,
    summary="Scrape a single Drug Safety Update",
    description="Start a background task that fetches one MHRA Drug Safety Update article by slug.",
)
async def scrape_one_safety_update(slug: str) -> TaskResponse:
    """Enqueue a single MHRA Drug Safety Update scrape."""
    scrape_key = f"{DSU_DOMAIN}:{slug}"
    existing = get_active_scrape(scrape_key)
    if existing:
        raise HTTPException(409, detail={"message": f"A scrape for {slug} is already running", "task_id": existing.task_id})
    task = create_task()
    set_active_scrape(scrape_key, task.task_id)
    async_task = asyncio.create_task(scrape_one_dsu(slug, task.task_id, scrape_key))
    register_async_task(task.task_id, async_task)
    return TaskResponse(task_id=task.task_id)


@router.get(
    "/",
    response_model=list[ItemSummary],
    summary="List scraped Drug Safety Updates",
    description="Return slug and name for every previously scraped MHRA Drug Safety Update.",
)
async def list_safety_updates() -> list[ItemSummary]:
    """List all scraped MHRA Drug Safety Update articles."""
    pool = db.get_pool()
    rows = await db.list_pages(pool, DSU_DOMAIN)
    return [ItemSummary(slug=r["slug"], name=r["name"]) for r in rows]


@router.get(
    "/{slug}",
    response_model=ItemContent,
    summary="Get a scraped Drug Safety Update",
    description="Retrieve full markdown content and metadata for a single MHRA Drug Safety Update.",
)
async def get_safety_update(slug: str) -> ItemContent:
    """Fetch one scraped MHRA Drug Safety Update by slug."""
    pool = db.get_pool()
    row = await db.get_page(pool, DSU_DOMAIN, slug)
    if row is None:
        raise HTTPException(404, f"{slug} not found")
    return ItemContent(
        slug=row["slug"], name=row["name"], url=row["url"],
        page_last_reviewed=row["page_last_reviewed"],
        next_review_due=row["next_review_due"], markdown=row["markdown"],
    )


@router.delete("/{slug}", summary="Delete a scraped Drug Safety Update")
async def delete_safety_update(slug: str) -> dict:
    """Remove a scraped MHRA Drug Safety Update from the database."""
    pool = db.get_pool()
    deleted = await db.delete_page(pool, DSU_DOMAIN, slug)
    if not deleted:
        raise HTTPException(404, f"{slug} not found")
    return {"deleted": slug}
