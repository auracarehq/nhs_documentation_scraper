"""GOV.UK Content API client for MHRA Drug Safety Updates."""

from __future__ import annotations

import json

from domains.mhra.config import DSU_DOC_TYPE, GOVUK_CONTENT_URL, GOVUK_SEARCH_URL
from scraper.client import fetch


async def search_drug_safety_updates(count: int = 100, start: int = 0) -> dict:
    """Fetch a page of Drug Safety Update listings from the GOV.UK search API."""
    url = (
        f"{GOVUK_SEARCH_URL}"
        f"?filter_content_store_document_type={DSU_DOC_TYPE}"
        f"&count={count}&start={start}"
    )
    return json.loads(await fetch(url))


async def fetch_article_content(link: str) -> dict:
    """Fetch full article detail from the GOV.UK Content API."""
    return json.loads(await fetch(f"{GOVUK_CONTENT_URL}{link}"))
