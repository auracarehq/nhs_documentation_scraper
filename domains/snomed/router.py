"""Router for SNOMED CT concept search and local caching."""

from __future__ import annotations

import db
from domains.snomed.config import DEFAULT_LIMIT, MAX_LIMIT
from domains.snomed.models import ConceptDetail, ConceptSearchResult, ConceptSummary
from domains.snomed.service import fetch_and_cache, get_or_fetch, search
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/snomed", tags=["SNOMED CT"])


@router.get(
    "/concepts",
    response_model=ConceptSearchResult,
    summary="Search SNOMED CT concepts",
    description=(
        "Search the SNOMED CT UK Clinical Edition by clinical term via the public "
        "Snowstorm API. Results are not cached — this always hits the live API."
    ),
)
async def search_concepts(
    q: str = Query(..., min_length=2, description="Clinical term to search for"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> ConceptSearchResult:
    """Search SNOMED CT by clinical term."""
    return await search(q, limit)


@router.get(
    "/cached",
    response_model=list[ConceptSummary],
    summary="List locally cached SNOMED CT concepts",
    description="Return all SNOMED CT concepts stored in the local PostgreSQL cache.",
)
async def list_cached_concepts() -> list[ConceptSummary]:
    """List all locally cached SNOMED CT concepts."""
    rows = await db.list_snomed_concepts()
    return [
        ConceptSummary(
            concept_id=r["concept_id"],
            preferred_term=r["preferred_term"],
            fsn=r["fsn"],
            active=r["active"],
        )
        for r in rows
    ]


@router.get(
    "/concepts/{concept_id}",
    response_model=ConceptDetail,
    summary="Get or fetch a SNOMED CT concept",
    description=(
        "Return the concept from the local cache if available; otherwise fetch from "
        "the Snowstorm API, cache the result, and return it."
    ),
)
async def get_concept(concept_id: str) -> ConceptDetail:
    """Fetch a SNOMED CT concept by ID, caching on first access."""
    try:
        return await get_or_fetch(concept_id)
    except Exception as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post(
    "/concepts/{concept_id}/cache",
    response_model=ConceptDetail,
    summary="Force-refresh a SNOMED CT concept cache entry",
    description="Explicitly fetch from the Snowstorm API and overwrite the local cache entry.",
)
async def cache_concept(concept_id: str) -> ConceptDetail:
    """Force-fetch and cache a SNOMED CT concept."""
    try:
        return await fetch_and_cache(concept_id)
    except Exception as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.delete(
    "/concepts/{concept_id}",
    summary="Remove a SNOMED CT concept from the local cache",
)
async def delete_concept(concept_id: str) -> dict:
    """Remove a SNOMED CT concept from the local cache."""
    deleted = await db.delete_snomed_concept(concept_id)
    if not deleted:
        raise HTTPException(404, f"Concept {concept_id} not in cache")
    return {"deleted": concept_id}
