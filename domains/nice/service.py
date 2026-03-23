"""Shared scrape orchestration for NICE domains (CKS, BNF, BNFc)."""

from __future__ import annotations

import asyncio

import db
from domains.nice.config import DOMAINS
from domains.nice.scraper import scrape_nice_index
from scraper.markdown import page_to_markdown
from scraper.page import scrape_page
from tasks import clear_active_scrape, update_task


async def scrape_all(domain: str, task_id: str, scrape_key: str, *, force: bool = False) -> None:
    """Scrape every item from a NICE domain listing index."""
    cfg = DOMAINS[domain]
    try:
        update_task(task_id, status="running", message="Fetching index...")
        entries = await scrape_nice_index(cfg["index_url"], cfg["base_url"], cfg["link_prefix"])
        update_task(task_id, total=len(entries), message=f"Found {len(entries)} items")

        pool = db.get_pool()
        skipped = 0
        for i, entry in enumerate(entries):
            if not force:
                existing = await db.get_page(pool, domain, entry.slug)
                if existing:
                    skipped += 1
                    update_task(task_id, done=i + 1, message=f"Skipped {entry.slug} (already exists)")
                    continue
            try:
                page_data = await scrape_page(entry.url, name=entry.name)
                markdown = page_to_markdown(page_data)
                await db.upsert_page(
                    pool, domain, entry.slug,
                    name=page_data.name, url=page_data.url,
                    page_last_reviewed=page_data.page_last_reviewed or "",
                    next_review_due=page_data.next_review_due or "",
                    markdown=markdown,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                update_task(task_id, message=f"Error on {entry.slug}: {exc}")
            update_task(task_id, done=i + 1)

        msg = "Done" if not skipped else f"Done ({skipped} skipped, already existed)"
        update_task(task_id, status="completed", message=msg)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        update_task(task_id, status="failed", message=str(exc))
    finally:
        clear_active_scrape(scrape_key)


async def scrape_one(domain: str, slug: str, task_id: str, scrape_key: str) -> None:
    """Scrape a single NICE item by slug."""
    cfg = DOMAINS[domain]
    try:
        update_task(task_id, status="running", total=1, message=f"Scraping {slug}...")
        url = cfg["base_url"].rstrip("/") + cfg["item_path"].format(slug=slug)
        page_data = await scrape_page(url, name=slug)
        markdown = page_to_markdown(page_data)
        pool = db.get_pool()
        await db.upsert_page(
            pool, domain, slug,
            name=page_data.name, url=page_data.url,
            page_last_reviewed=page_data.page_last_reviewed or "",
            next_review_due=page_data.next_review_due or "",
            markdown=markdown,
        )
        update_task(task_id, status="completed", done=1, message="Done")
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        update_task(task_id, status="failed", message=str(exc))
    finally:
        clear_active_scrape(scrape_key)
