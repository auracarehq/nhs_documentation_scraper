"""Snowstorm REST API client for SNOMED CT concept lookup."""

from __future__ import annotations

import json

from domains.snomed.config import MAX_LIMIT, SNOWSTORM_BASE, UK_BRANCH_ENCODED
from scraper.client import fetch


async def search_concepts(term: str, limit: int = 25) -> dict:
    """Search SNOMED CT concepts by clinical term (UK edition)."""
    capped = min(limit, MAX_LIMIT)
    url = (
        f"{SNOWSTORM_BASE}/{UK_BRANCH_ENCODED}/concepts"
        f"?term={term}&activeFilter=true&limit={capped}&returnIdOnly=false"
    )
    return json.loads(await fetch(url))


async def get_concept(concept_id: str) -> dict:
    """Fetch the full browser representation of a single SNOMED CT concept."""
    url = f"{SNOWSTORM_BASE}/browser/{UK_BRANCH_ENCODED}/concepts/{concept_id}"
    return json.loads(await fetch(url))
