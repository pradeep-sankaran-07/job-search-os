"""Target-company careers-page scraping helpers.

For each Tier 1 company in the target-companies file (accepted filenames
include Target Companies.pdf, target-companies.md, target-companies.pdf,
target-companies.txt, target-companies.docx), the daily-search skill
navigates to the careers URL via Playwright MCP and looks for open roles
matching the user's target titles.

Career pages vary wildly in structure. This module provides:
  - A small list of well-known ATS host families with reliable selectors
  - Keyword matching utilities (title contains any target title + seniority)
  - URL normalisation

The skill handles the MCP navigation itself; this module is pure data.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# ATS host families and suggested "job title selector" for DOM extraction.
# These are hints for the skill; if a careers page uses one of these ATSes,
# the skill can pull job titles more reliably.
ATS_FAMILIES = {
    "greenhouse.io": {"title_selector": ".opening a", "url_pattern": "/boards/"},
    "boards.greenhouse.io": {"title_selector": ".opening a", "url_pattern": None},
    "lever.co": {"title_selector": ".posting-title", "url_pattern": "jobs.lever.co"},
    "ashbyhq.com": {"title_selector": "a[class*='_title_']", "url_pattern": "jobs.ashbyhq.com"},
    "myworkdayjobs.com": {"title_selector": "[data-automation-id='jobTitle']", "url_pattern": None},
    "teamtailor": {"title_selector": ".job-title, h3", "url_pattern": None},
    "bamboohr.com": {"title_selector": ".BambooHR-ATS-Jobs-Item-Title", "url_pattern": None},
    "smartrecruiters.com": {"title_selector": ".opening-job-title", "url_pattern": None},
    "pinpointhq.com": {"title_selector": ".job-title", "url_pattern": None},
    "personio.de": {"title_selector": ".jobposition-title", "url_pattern": None},
    "jobs.workable.com": {"title_selector": "a[data-ui='job-title']", "url_pattern": None},
    "recruitee.com": {"title_selector": ".job-card__title", "url_pattern": None},
}


def detect_ats_family(careers_url: str) -> str | None:
    """Return the ATS family name for a careers URL, or None if unknown."""
    try:
        host = urlparse(careers_url).hostname or ""
    except Exception:
        return None
    host = host.lower()
    for family in ATS_FAMILIES:
        if host.endswith(family):
            return family
    return None


def title_matches_any(page_title: str, target_titles: list[str]) -> bool:
    """Return True if any target title word is found in page_title (case-insensitive)."""
    norm = (page_title or "").lower()
    for t in target_titles:
        key = t.lower().strip()
        if not key:
            continue
        if key in norm:
            return True
        # Also check the core token (e.g. "Head of Product" → "head of product" → tokens)
        tokens = [w for w in key.split() if len(w) > 2]
        if tokens and all(tok in norm for tok in tokens):
            return True
    return False


def is_above_seniority(title: str, min_seniority: str) -> bool:
    """Return True if the title clearly indicates >= min_seniority.

    Heuristic only. The daily-search skill uses this as a soft filter.
    """
    t = (title or "").lower()
    seniority_markers = {
        "ic": [""],
        "manager": ["manager", "lead", "head", "director", "vp", "chief", "svp"],
        "director": ["director", "head of", "vp", "chief", "svp"],
        "vp": ["vp", "chief", "svp", "cpo", "cto", "ceo"],
        "cxo": ["chief", "cpo", "cto", "ceo", "president"],
    }
    markers = seniority_markers.get((min_seniority or "").lower(), [])
    if not markers or markers == [""]:
        return True
    return any(m in t for m in markers)


def normalize_careers_url(url: str) -> str:
    """Strip tracking params, trailing slashes."""
    if not url:
        return ""
    # Simple strip; don't try to be clever with query params — some are needed.
    return url.strip().rstrip("/")


# Common "no jobs found" phrases across career pages — the skill checks for
# these so it can record a clean "zero hits" rather than treating the page as
# broken.
EMPTY_STATE_PHRASES = [
    "no open positions",
    "no openings",
    "no current openings",
    "no positions available",
    "we don't have any open roles",
    "we are not currently hiring",
    "all positions have been filled",
    "ingen ledige stillinger",
    "vi har for øyeblikket ingen ledige stillinger",
]


def is_empty_state(body_text: str) -> bool:
    norm = (body_text or "").lower()
    return any(p in norm for p in EMPTY_STATE_PHRASES)
