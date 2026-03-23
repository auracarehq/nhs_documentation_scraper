"""SNOMED CT concept lookup and local cache management."""

from __future__ import annotations

import json

import db
from domains.snomed.client import get_concept, search_concepts
from domains.snomed.config import DEFAULT_LIMIT
from domains.snomed.models import ConceptDetail, ConceptSearchResult, ConceptSummary


def _extract_hierarchy(concept: dict) -> str:
    """Extract the SNOMED hierarchy tag from the fully specified name parenthetical."""
    fsn_obj = concept.get("fsn", {})
    fsn_term = fsn_obj.get("term", "") if isinstance(fsn_obj, dict) else ""
    if "(" in fsn_term:
        return fsn_term.rsplit("(", 1)[-1].rstrip(")")
    return ""


def _to_summary(concept: dict) -> ConceptSummary:
    """Map a Snowstorm concept dict to a ConceptSummary."""
    pt_obj = concept.get("pt", {})
    fsn_obj = concept.get("fsn", {})
    return ConceptSummary(
        concept_id=concept.get("conceptId", ""),
        preferred_term=pt_obj.get("term", "") if isinstance(pt_obj, dict) else "",
        fsn=fsn_obj.get("term", "") if isinstance(fsn_obj, dict) else "",
        active=concept.get("active", True),
    )


async def search(term: str, limit: int = DEFAULT_LIMIT) -> ConceptSearchResult:
    """Search SNOMED CT concepts by clinical term (always hits the live API)."""
    data = await search_concepts(term, limit)
    items = [_to_summary(c) for c in data.get("items", [])]
    return ConceptSearchResult(
        items=items,
        total=data.get("total", 0),
        limit=data.get("limit", limit),
        offset=data.get("offset", 0),
    )


async def fetch_and_cache(concept_id: str) -> ConceptDetail:
    """Fetch a concept from the Snowstorm API and write it to the local cache."""
    concept = await get_concept(concept_id)
    summary = _to_summary(concept)
    hierarchy = _extract_hierarchy(concept)
    raw = json.dumps(concept)
    await db.cache_snomed_concept(
        concept_id=summary.concept_id,
        preferred_term=summary.preferred_term,
        fsn=summary.fsn,
        hierarchy=hierarchy,
        active=summary.active,
        raw_json=raw,
    )
    return ConceptDetail(**summary.model_dump(), hierarchy=hierarchy, raw_json=raw, cached=True)


async def get_or_fetch(concept_id: str) -> ConceptDetail:
    """Return the cached concept if present, otherwise fetch from the Snowstorm API."""
    cached = await db.get_snomed_concept(concept_id)
    if cached:
        return ConceptDetail(
            concept_id=cached["concept_id"],
            preferred_term=cached["preferred_term"],
            fsn=cached["fsn"],
            hierarchy=cached["hierarchy"],
            active=cached["active"],
            raw_json=cached["raw_json"],
            cached=True,
        )
    return await fetch_and_cache(concept_id)
