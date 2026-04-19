"""LinkedIn adapter helpers.

LinkedIn is driven by the daily-search skill via the `claude-in-chrome`
extension (NOT Playwright MCP). LinkedIn blocks both JobSpy and headless
browsers; the only reliable approach is to use the user's already-logged-in
Chrome session via the extension.

This module provides:
  - Search URL builder for LinkedIn /jobs/search/
  - Card parser (converts a page-text or DOM snapshot of a card into a
    candidate dict)
  - Location geoId hints (optional; LinkedIn accepts ?location= text)

The skill:
  1. Verifies `mcp__Claude_in_Chrome__navigate` is available. If not, skips.
  2. For each (title, location) from profile.yaml, calls search_url() and
     navigates via the Chrome MCP.
  3. For each result card extracted from the page, calls parse_card().
  4. Filters out promoted-only listings and "Easy Apply" aggregators when the
     same role exists on the company careers page.
  5. Paginates up to 3 pages per query.
"""
from __future__ import annotations

from urllib.parse import quote_plus

BASE_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

# Common location shortcuts. LinkedIn accepts free-text in ?location=, so this
# is just a cleanup table.
LOCATION_NORMALISATION = {
    "oslo": "Oslo, Norway",
    "norway": "Norway",
    "nordic": "Nordics",
    "remote europe": "European Union",
    "remote, europe": "European Union",
    "remote global": "Worldwide",
}


def search_url(keywords: str, location: str | None = None, f_TPR: str = "r604800") -> str:
    """Build a LinkedIn /jobs/search/ URL.

    Args:
        keywords: job title keywords (e.g. "Head of Product")
        location: free-text location; normalised via LOCATION_NORMALISATION
        f_TPR: time-posted filter. Default r604800 = "past week".
               Other values: r86400 (24h), r2592000 (30d).
    """
    loc = (location or "").strip()
    loc = LOCATION_NORMALISATION.get(loc.lower(), loc)
    parts = [f"keywords={quote_plus(keywords)}"]
    if loc:
        parts.append(f"location={quote_plus(loc)}")
    if f_TPR:
        parts.append(f"f_TPR={f_TPR}")
    return BASE_SEARCH_URL + "?" + "&".join(parts)


def parse_card(raw: dict) -> dict | None:
    """Convert a LinkedIn result card dict into a candidate dict.

    Expected input fields:
      - title: str
      - company: str | None
      - location: str | None
      - url: str (the LinkedIn /jobs/view/<id>/ URL)
      - posted: str | None
      - easy_apply: bool | None
    """
    url = (raw.get("url") or "").strip()
    title = (raw.get("title") or "").strip()
    company = (raw.get("company") or "").strip()

    if not url or not title or not company:
        return None

    # Keep only real job URLs.
    if "/jobs/view/" not in url and "currentJobId=" not in url:
        return None

    return {
        "title": title,
        "company": company,
        "location": (raw.get("location") or "").strip() or None,
        "url": url,
        "date_posted": (raw.get("posted") or "").strip() or None,
        "source": "linkedin",
        "easy_apply": bool(raw.get("easy_apply")),
        "description": "",  # filled by click-through in the skill
    }


def extension_available_check_snippet() -> str:
    """The skill checks for Chrome MCP by listing tools. This is a note to the
    skill — no code. The relevant tools are prefixed with
    `mcp__Claude_in_Chrome__`."""
    return "Check that mcp__Claude_in_Chrome__navigate appears in the available tools list."
