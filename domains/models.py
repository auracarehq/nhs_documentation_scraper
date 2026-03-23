"""Shared response models used across all domains."""

from __future__ import annotations

from pydantic import BaseModel


class TaskResponse(BaseModel):
    """Response returned when a background task is created."""

    task_id: str


class TaskStatusResponse(BaseModel):
    """Full status of a background task."""

    task_id: str
    status: str
    done: int
    total: int
    message: str
    created_at: str
    updated_at: str


class SearchResult(BaseModel):
    """A single search result with domain context."""

    slug: str
    name: str
    domain: str


class ItemSummary(BaseModel):
    """Slug and display name for a scraped item."""

    slug: str
    name: str


class ItemContent(BaseModel):
    """Full content and metadata for a scraped item."""

    slug: str
    name: str
    url: str
    page_last_reviewed: str
    next_review_due: str
    markdown: str
