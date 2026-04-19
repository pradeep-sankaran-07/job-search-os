"""Finn.no adapter helpers.

Finn.no is driven by the daily-search skill via Playwright MCP tool calls
(headless Chromium). This module provides:

  - Norwegian-language title translations for common product-leadership titles
  - Staffing-agency blocklist (the Norwegian market has many; filtering these
    early prevents noise in the tracker)
  - Search URL builder
  - Card parser (converts a Playwright DOM snapshot of a result card into a
    candidate dict)

The skill:
  1. Loads profile.yaml, collects target_titles.
  2. Expands each target title with Norwegian equivalents via translate_title().
  3. For each (title, location), calls search_url() and navigates via MCP.
  4. For each result card extracted from the page DOM, calls parse_card().
  5. Filters out cards whose company matches is_staffing_agency().
  6. Paginates (up to 5 pages per query).
"""
from __future__ import annotations

from urllib.parse import urlencode

BASE_SEARCH_URL = "https://www.finn.no/job/fulltime/search.html"

# Map common English product-leadership titles to Norwegian equivalents.
# When a Norwegian-language location is in the user's profile, the skill should
# include these translated variants in addition to the English ones.
TITLE_TRANSLATIONS = {
    "head of product": ["produktsjef", "produktdirektør"],
    "vp product": ["produktdirektør", "viseproduktdirektør"],
    "chief product officer": ["produktdirektør", "CPO"],
    "director of product": ["produktdirektør"],
    "director product": ["produktdirektør"],
    "svp product": ["produktdirektør"],
    "product manager": ["produktsjef"],
    "senior product manager": ["senior produktsjef"],
    # Add more as the user base grows.
}

# Norwegian staffing agencies — reject postings from these "companies" since
# they are recruiters reposting client roles with no direct-apply path.
STAFFING_AGENCIES_NO = {
    "academic work",
    "academic work norge",
    "manpowergroup",
    "manpower",
    "experis",
    "adecco",
    "adecco norge",
    "randstad",
    "randstad norge",
    "xtra personell",
    "xtrapersonell",
    "kelly services",
    "proffice",
    "right people",
    "worknorway",
    "bemanningsbyrået",
    "jobzone",
    "harvey nash",
    "testhuset",
    "istrid",
    "headvisor",
}


def translate_title(title: str) -> list[str]:
    """Return the input title plus any Norwegian equivalents."""
    out = [title]
    key = title.lower().strip()
    if key in TITLE_TRANSLATIONS:
        out.extend(TITLE_TRANSLATIONS[key])
    return out


def search_url(query: str, location: str | None = None) -> str:
    """Build a Finn.no full-time job search URL.

    Finn supports query and occupation filters via URL params; for v0.1 we
    stick to a simple keyword search.
    """
    params = {"q": query}
    if location:
        params["location"] = location
    return f"{BASE_SEARCH_URL}?{urlencode(params)}"


def is_staffing_agency(company: str) -> bool:
    c = (company or "").lower().strip()
    if c in STAFFING_AGENCIES_NO:
        return True
    # Partial match for obvious markers.
    for needle in ("personell", "bemanning", "staffing", "recruitment"):
        if needle in c:
            return True
    return False


def parse_card(raw: dict) -> dict | None:
    """Convert a Playwright-extracted result card into a candidate dict.

    Expected input fields (from the skill's DOM extraction):
      - title: str
      - company: str | None
      - location: str | None
      - url: str (direct https://www.finn.no/job/ad/... URL)
      - posted: str | None
    """
    url = (raw.get("url") or "").strip()
    title = (raw.get("title") or "").strip()
    company = (raw.get("company") or "").strip()
    if not url or not title or not company:
        return None
    if not url.startswith("https://www.finn.no/job/ad/") and "/job/fulltime/ad/" not in url:
        # Skip non-job-ad URLs (e.g. employer landing pages, saved searches).
        return None
    if is_staffing_agency(company):
        return None
    return {
        "title": title,
        "company": company,
        "location": (raw.get("location") or "").strip() or None,
        "url": url,
        "date_posted": (raw.get("posted") or "").strip() or None,
        "source": "finn.no",
        "description": "",  # filled by click-through in the skill
    }
