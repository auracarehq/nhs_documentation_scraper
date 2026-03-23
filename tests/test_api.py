from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with patch("db.init_db", new_callable=AsyncMock), \
         patch("db.close_db", new_callable=AsyncMock):
        with TestClient(app) as c:
            yield c


def _mock_db_row(slug, name, domain="conditions", url="", markdown="# Content", **extra):
    """Create a dict that mimics a DB row."""
    return {
        "slug": slug, "name": name, "domain": domain, "url": url,
        "page_last_reviewed": "", "next_review_due": "", "markdown": markdown,
        **extra,
    }


def test_list_empty(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/conditions/")
        assert resp.status_code == 200
        assert resp.json() == []


def test_list_with_items(client):
    rows = [
        _mock_db_row("acne", "Acne"),
        _mock_db_row("asthma", "Asthma"),
    ]
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=rows):
        resp = client.get("/conditions/")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2
        slugs = {i["slug"] for i in items}
        assert slugs == {"acne", "asthma"}


def test_get_item(client):
    row = _mock_db_row("acne", "Acne", markdown="# Acne\nContent here.")
    with patch("db.get_pool"), patch("db.get_page", new_callable=AsyncMock, return_value=row):
        resp = client.get("/conditions/acne")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "acne"
        assert data["name"] == "Acne"
        assert "# Acne" in data["markdown"]


def test_get_item_not_found(client):
    with patch("db.get_pool"), patch("db.get_page", new_callable=AsyncMock, return_value=None):
        resp = client.get("/conditions/nonexistent")
        assert resp.status_code == 404


def test_delete_item(client):
    with patch("db.get_pool"), patch("db.delete_page", new_callable=AsyncMock, return_value=True):
        resp = client.delete("/conditions/acne")
        assert resp.status_code == 200
        assert resp.json() == {"deleted": "acne"}


def test_delete_not_found(client):
    with patch("db.get_pool"), patch("db.delete_page", new_callable=AsyncMock, return_value=False):
        resp = client.delete("/conditions/nonexistent")
        assert resp.status_code == 404


def test_scrape_single_returns_task_id(client):
    with patch("domains.nhs.service.scrape_page", new_callable=AsyncMock) as mock_scrape:
        from scraper.page import PageData, Section
        mock_scrape.return_value = PageData(
            name="Acne", url="https://www.nhs.uk/conditions/acne/",
            sections=[Section(title="", html="<p>Content</p>")],
        )
        resp = client.post("/conditions/scrape/acne")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data


def test_scrape_all_returns_task_id(client):
    with patch("domains.nhs.service.scrape_index", new_callable=AsyncMock) as mock_index:
        mock_index.return_value = []
        resp = client.post("/conditions/scrape")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data


def test_task_status(client):
    from tasks import create_task
    task = create_task()
    resp = client.get(f"/tasks/{task.task_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_task_not_found(client):
    resp = client.get("/tasks/nonexistent")
    assert resp.status_code == 404


def test_symptoms_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/symptoms/")
        assert resp.status_code == 200


def test_medicines_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/medicines/")
        assert resp.status_code == 200


def test_treatments_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/treatments/")
        assert resp.status_code == 200


def test_search_empty_query(client):
    resp = client.get("/search")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_returns_matching(client):
    rows = [_mock_db_row("acne", "Acne", domain="conditions")]
    with patch("db.get_pool"), patch("db.search_pages", new_callable=AsyncMock, return_value=rows):
        resp = client.get("/search?q=acne")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["slug"] == "acne"
        assert results[0]["name"] == "Acne"
        assert results[0]["domain"] == "conditions"


def test_search_cross_domain(client):
    rows = [
        _mock_db_row("acne", "Acne", domain="conditions"),
        _mock_db_row("acne-gel", "Acne Gel", domain="medicines"),
    ]
    with patch("db.get_pool"), patch("db.search_pages", new_callable=AsyncMock, return_value=rows):
        resp = client.get("/search?q=acne")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 2
        domains = {r["domain"] for r in results}
        assert domains == {"conditions", "medicines"}


# ---------------------------------------------------------------------------
# NICE routers
# ---------------------------------------------------------------------------

def test_nice_cks_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/nice/cks/")
        assert resp.status_code == 200


def test_nice_bnf_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/nice/bnf/")
        assert resp.status_code == 200


def test_nice_bnfc_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/nice/bnfc/")
        assert resp.status_code == 200


def test_nice_cks_get_not_found(client):
    with patch("db.get_pool"), patch("db.get_page", new_callable=AsyncMock, return_value=None):
        resp = client.get("/nice/cks/nonexistent")
        assert resp.status_code == 404


def test_nice_bnf_scrape_returns_task_id(client):
    with patch("domains.nice.service.scrape_nice_index", new_callable=AsyncMock, return_value=[]):
        resp = client.post("/nice/bnf/scrape")
        assert resp.status_code == 200
        assert "task_id" in resp.json()


# ---------------------------------------------------------------------------
# MHRA router
# ---------------------------------------------------------------------------

def test_mhra_dsu_router_exists(client):
    with patch("db.get_pool"), patch("db.list_pages", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/mhra/drug-safety-updates/")
        assert resp.status_code == 200


def test_mhra_dsu_get_not_found(client):
    with patch("db.get_pool"), patch("db.get_page", new_callable=AsyncMock, return_value=None):
        resp = client.get("/mhra/drug-safety-updates/nonexistent")
        assert resp.status_code == 404


def test_mhra_dsu_scrape_returns_task_id(client):
    with patch("domains.mhra.service._fetch_all_listings", new_callable=AsyncMock, return_value=[]):
        resp = client.post("/mhra/drug-safety-updates/scrape")
        assert resp.status_code == 200
        assert "task_id" in resp.json()


# ---------------------------------------------------------------------------
# SNOMED CT router
# ---------------------------------------------------------------------------

def test_snomed_search_missing_query(client):
    resp = client.get("/snomed/concepts")
    assert resp.status_code == 422


def test_snomed_search_too_short(client):
    resp = client.get("/snomed/concepts?q=a")
    assert resp.status_code == 422


def test_snomed_search_returns_result(client):
    mock_result = {
        "items": [{"conceptId": "73211009", "active": True,
                   "pt": {"term": "Diabetes mellitus"}, "fsn": {"term": "Diabetes mellitus (disorder)"}}],
        "total": 1, "limit": 25, "offset": 0,
    }
    with patch("domains.snomed.service.search_concepts", new_callable=AsyncMock, return_value=mock_result):
        resp = client.get("/snomed/concepts?q=diabetes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["concept_id"] == "73211009"
        assert data["items"][0]["preferred_term"] == "Diabetes mellitus"


def test_snomed_list_cached_empty(client):
    with patch("db.list_snomed_concepts", new_callable=AsyncMock, return_value=[]):
        resp = client.get("/snomed/cached")
        assert resp.status_code == 200
        assert resp.json() == []


def test_snomed_get_concept_from_cache(client):
    cached = {
        "concept_id": "73211009", "preferred_term": "Diabetes mellitus",
        "fsn": "Diabetes mellitus (disorder)", "hierarchy": "disorder",
        "active": True, "raw_json": "{}", "cached_at": "2024-01-01T00:00:00+00:00",
    }
    with patch("db.get_snomed_concept", new_callable=AsyncMock, return_value=cached):
        resp = client.get("/snomed/concepts/73211009")
        assert resp.status_code == 200
        data = resp.json()
        assert data["concept_id"] == "73211009"
        assert data["hierarchy"] == "disorder"
        assert data["cached"] is True


def test_snomed_delete_concept_not_cached(client):
    with patch("db.delete_snomed_concept", new_callable=AsyncMock, return_value=False):
        resp = client.delete("/snomed/concepts/73211009")
        assert resp.status_code == 404
