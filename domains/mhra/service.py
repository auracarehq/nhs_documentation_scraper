"""Scrape orchestration for MHRA Drug Safety Updates via GOV.UK API."""

from __future__ import annotations

import asyncio

from markdownify import markdownify as md

import db
from domains.mhra.client import fetch_article_content, search_drug_safety_updates
from domains.mhra.config import DSU_DOMAIN, DSU_PAGE_SIZE, GOVUK_BASE_URL
from tasks import clear_active_scrape, update_task


def _article_to_markdown(article: dict) -> str:
    """Convert a GOV.UK Content API response body to markdown."""
    details = article.get("details", {})
    body = details.get("body", "") or details.get("introduction", "")
    if not body:
        return ""
    return md(body, heading_style="ATX", strip=["img", "script", "style"])


async def _fetch_all_listings() -> list[dict]:
    """Paginate through the GOV.UK search API and return all DSU listings."""
    all_items: list[dict] = []
    start = 0
    while True:
        data = await search_drug_safety_updates(count=DSU_PAGE_SIZE, start=start)
        all_items.extend(data.get("results", []))
        start += DSU_PAGE_SIZE
        if start >= data.get("total", 0):
            break
    return all_items


async def scrape_all_dsu(task_id: str, scrape_key: str, *, force: bool = False) -> None:
    """Scrape every MHRA Drug Safety Update article."""
    try:
        update_task(task_id, status="running", message="Fetching Drug Safety Update index...")
        listings = await _fetch_all_listings()
        update_task(task_id, total=len(listings), message=f"Found {len(listings)} articles")

        pool = db.get_pool()
        skipped = 0
        for i, item in enumerate(listings):
            slug = item.get("link", "").rstrip("/").split("/")[-1]
            if not slug:
                update_task(task_id, done=i + 1)
                continue
            if not force:
                existing = await db.get_page(pool, DSU_DOMAIN, slug)
                if existing:
                    skipped += 1
                    update_task(task_id, done=i + 1, message=f"Skipped {slug}")
                    continue
            try:
                article = await fetch_article_content(item["link"])
                markdown = _article_to_markdown(article)
                title = article.get("title", item.get("title", slug))
                published = article.get("public_updated_at", item.get("public_timestamp", ""))
                await db.upsert_page(
                    pool, DSU_DOMAIN, slug,
                    name=title,
                    url=f"{GOVUK_BASE_URL}{item['link']}",
                    page_last_reviewed=published,
                    next_review_due="",
                    markdown=markdown,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                update_task(task_id, message=f"Error on {slug}: {exc}")
            update_task(task_id, done=i + 1)

        msg = "Done" if not skipped else f"Done ({skipped} skipped)"
        update_task(task_id, status="completed", message=msg)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        update_task(task_id, status="failed", message=str(exc))
    finally:
        clear_active_scrape(scrape_key)


async def scrape_one_dsu(slug: str, task_id: str, scrape_key: str) -> None:
    """Scrape a single MHRA Drug Safety Update article by slug."""
    try:
        update_task(task_id, status="running", total=1, message=f"Fetching {slug}...")
        link = f"/drug-safety-update/{slug}"
        article = await fetch_article_content(link)
        markdown = _article_to_markdown(article)
        title = article.get("title", slug)
        published = article.get("public_updated_at", "")
        pool = db.get_pool()
        await db.upsert_page(
            pool, DSU_DOMAIN, slug,
            name=title,
            url=f"{GOVUK_BASE_URL}{link}",
            page_last_reviewed=published,
            next_review_due="",
            markdown=markdown,
        )
        update_task(task_id, status="completed", done=1, message="Done")
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        update_task(task_id, status="failed", message=str(exc))
    finally:
        clear_active_scrape(scrape_key)
