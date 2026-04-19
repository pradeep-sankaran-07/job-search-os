"""Run python-jobspy against Indeed + Glassdoor using the user's profile.

Reads profile.yaml, sources.yaml, and writes candidate jobs to
<user_dir>/logs/jobspy_results-<YYYY-MM-DD>.json.

Best-effort: JobSpy gets blocked on both Indeed and Glassdoor sometimes.
Exceptions per site/term/location are caught and logged, not raised.

Forked and generalised from Pradeep's personal jobspy_run.py.

Usage:
    python3 jobspy_boards.py <user_dir>
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import yaml
from jobspy import scrape_jobs


def load_profile(user_dir: Path) -> dict:
    return yaml.safe_load((user_dir / "profile.yaml").read_text())


def load_sources(user_dir: Path) -> dict:
    return yaml.safe_load((user_dir / "sources.yaml").read_text())


def enabled_sites(sources: dict) -> list[str]:
    """Return the subset of {indeed, glassdoor} that are enabled."""
    out = []
    for name in ("indeed", "glassdoor"):
        entry = sources.get("sources", {}).get(name, {})
        if entry.get("enabled") and entry.get("method") == "jobspy":
            out.append(name)
    return out


def country_for_indeed(sources: dict) -> str | None:
    return sources.get("sources", {}).get("indeed", {}).get("country_code")


def run(user_dir: Path) -> int:
    profile = load_profile(user_dir)
    sources = load_sources(user_dir)

    sites = enabled_sites(sources)
    if not sites:
        print("[jobspy] No JobSpy sites enabled — nothing to do.")
        return 0

    terms: list[str] = [t for t in (profile.get("target_titles") or []) if t]
    locations: list[str] = [l for l in (profile.get("target_locations") or []) if l]
    hard_filters: list[str] = [f.lower() for f in (profile.get("hard_filters") or []) if f]
    min_seniority = (profile.get("min_seniority") or {}).get("value", "").lower()

    if not terms or not locations:
        print("[jobspy] profile.yaml missing target_titles or target_locations.")
        return 2

    country_indeed = country_for_indeed(sources)
    # python-jobspy accepts a limited set of country names; if the user's
    # sources.yaml specifies something unrecognised, drop it rather than crashing.
    JOBSPY_COUNTRIES = {
        "argentina", "australia", "austria", "bahrain", "bangladesh", "belgium",
        "bulgaria", "brazil", "canada", "chile", "china", "colombia",
        "costa rica", "croatia", "cyprus", "czech republic", "czechia",
        "denmark", "ecuador", "egypt", "estonia", "finland", "france",
        "germany", "greece", "hong kong", "hungary", "india", "indonesia",
        "ireland", "israel", "italy", "japan", "kuwait", "latvia", "lithuania",
        "luxembourg", "malaysia", "malta", "mexico", "morocco", "netherlands",
        "new zealand", "nigeria", "norway", "oman", "pakistan", "panama",
        "peru", "philippines", "poland", "portugal", "qatar", "romania",
        "saudi arabia", "singapore", "slovakia", "slovenia", "south africa",
        "south korea", "spain", "sweden", "switzerland", "taiwan", "thailand",
        "türkiye", "turkey", "ukraine", "united arab emirates", "uk",
        "united kingdom", "usa", "us", "united states", "uruguay", "venezuela",
        "vietnam", "usa/ca", "worldwide",
    }
    if country_indeed and country_indeed.lower() not in JOBSPY_COUNTRIES:
        print(f"[jobspy] Unknown country_indeed '{country_indeed}' — running without it.")
        country_indeed = None

    frames = []
    log_lines = []
    start = time.time()
    budget_s = 480  # 8-minute cap

    def log(msg: str) -> None:
        print(msg, flush=True)
        log_lines.append(msg)

    for term in terms:
        for loc in locations:
            if time.time() - start > budget_s:
                log(f"[budget] Hit 8-minute cap, skipping {term} / {loc}")
                continue
            try:
                log(f"[scrape] {term} / {loc} (sites: {','.join(sites)})")
                df = scrape_jobs(
                    site_name=sites,
                    search_term=term,
                    location=loc,
                    results_wanted=20,
                    hours_old=168,
                    country_indeed=country_indeed,
                    linkedin_fetch_description=False,
                    verbose=0,
                )
                if df is not None and not df.empty:
                    df["_search_term"] = term
                    df["_search_location"] = loc
                    frames.append(df)
                    log(f"  -> {len(df)} rows")
                else:
                    log("  -> 0 rows")
            except Exception as e:
                log(f"  [warn] {e}")

    out_dir = user_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"jobspy_results-{date.today().isoformat()}.json"
    log_path = out_dir / f"jobspy_log-{date.today().isoformat()}.txt"

    if not frames:
        out_path.write_text("[]")
        log("No frames returned — writing empty list.")
        log_path.write_text("\n".join(log_lines))
        return 0

    jobs = pd.concat(frames, ignore_index=True)

    # Dedup
    jobs["_k"] = (
        jobs["company"].fillna("").str.lower().str.strip()
        + "||"
        + jobs["title"].fillna("").str.lower().str.strip()
    )
    jobs = jobs.drop_duplicates(subset="_k")
    log(f"Unique after dedup: {len(jobs)}")

    # Hard filter
    junior_below_director = {
        "ic": [],
        "manager": [],
        "director": ["senior product manager", "product owner", "associate pm",
                     "product analyst", "junior product"],
        "vp": ["senior product manager", "product owner", "associate pm",
               "product analyst", "junior product", "director of product",
               "head of product", "product manager"],
        "cxo": ["senior product manager", "product owner", "associate pm",
                "product analyst", "junior product", "director of product"],
    }.get(min_seniority, [])

    def bad(row) -> bool:
        text = f"{row.get('title','')} {row.get('description','')}".lower()
        if any(k in text for k in hard_filters):
            return True
        t = str(row.get("title", "")).lower()
        if junior_below_director and any(jt in t for jt in junior_below_director):
            # Allow upward titles (e.g. "Head of", "VP" in the title overrides).
            upward = ["head", "director", "vp", "chief", "svp"]
            if not any(u in t for u in upward):
                return True
        return False

    jobs["_filtered"] = jobs.apply(bad, axis=1)
    kept = jobs[~jobs["_filtered"]].copy()
    log(f"After hard filter: {len(kept)}")

    cols = ["title", "company", "location", "date_posted", "job_url", "site",
            "_search_term", "_search_location", "description"]
    have = [c for c in cols if c in kept.columns]
    records = kept[have].fillna("").to_dict(orient="records")
    for r in records:
        if "description" in r and isinstance(r["description"], str):
            r["description"] = r["description"][:600]

    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str))
    log(f"Wrote {len(records)} jobs to {out_path}")
    log_path.write_text("\n".join(log_lines))
    log(f"Elapsed: {time.time()-start:.1f}s")

    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: jobspy_boards.py <user_dir>")
        return 2
    return run(Path(argv[1]).expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main(sys.argv))
