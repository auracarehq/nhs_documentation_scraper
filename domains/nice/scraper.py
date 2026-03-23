"""NICE-specific index page parsing."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.client import fetch
from scraper.index import IndexEntry


def parse_nice_index(html: str, base_url: str, link_prefix: str) -> list[IndexEntry]:
    """Parse a NICE listing page and return entries whose href matches link_prefix."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("main") or soup
    entries: list[IndexEntry] = []
    seen: set[str] = set()

    for a_tag in container.find_all("a", href=True):
        href = str(a_tag["href"])
        if not href.startswith(link_prefix):
            continue
        name = a_tag.get_text(strip=True)
        if not name:
            continue
        slug = href.rstrip("/").split("/")[-1]
        if slug and slug not in seen:
            seen.add(slug)
            url = urljoin(base_url, href.rstrip("/") + "/")
            entries.append(IndexEntry(name=name, url=url, slug=slug))

    return entries


async def scrape_nice_index(index_url: str, base_url: str, link_prefix: str) -> list[IndexEntry]:
    """Fetch and parse a NICE listing page."""
    html = await fetch(index_url)
    return parse_nice_index(html, base_url, link_prefix)
