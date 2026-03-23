"""SNOMED CT Pydantic response models."""

from __future__ import annotations

from pydantic import BaseModel


class ConceptSummary(BaseModel):
    """Lightweight SNOMED CT concept with ID and display terms."""

    concept_id: str
    preferred_term: str
    fsn: str
    active: bool


class ConceptDetail(ConceptSummary):
    """Full SNOMED CT concept including hierarchy tag and raw Snowstorm payload."""

    hierarchy: str
    raw_json: str
    cached: bool = False


class ConceptSearchResult(BaseModel):
    """Paginated search results from the Snowstorm API."""

    items: list[ConceptSummary]
    total: int
    limit: int
    offset: int
