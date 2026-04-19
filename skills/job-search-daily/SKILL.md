---
name: job-search-daily
description: Run today's multi-source job search. Loads the user's tracker, searches Finn.no + LinkedIn + Indeed + Glassdoor against their profile, verifies each URL live, rates fit, drafts cover letters for Strong fits, updates tracker.xlsx and cover-letters.docx, and prints a summary. Runs without interrupting the user.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(python3:*)
  - Bash(node:*)
  - Bash(bash:*)
  - WebFetch
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
  - mcp__playwright__browser_press_key
  - mcp__playwright__browser_wait_for
  - mcp__playwright__browser_evaluate
  - mcp__playwright__browser_close
  - mcp__Claude_in_Chrome__navigate
  - mcp__Claude_in_Chrome__get_page_text
  - mcp__Claude_in_Chrome__read_page
  - mcp__Claude_in_Chrome__find
  - mcp__Claude_in_Chrome__javascript_tool
  - mcp__Claude_in_Chrome__tabs_create_mcp
  - mcp__Claude_in_Chrome__tabs_close_mcp
---

You are running the user's daily job search. This skill executes end-to-end without pausing for user input. Report at the end, not mid-run.

## Working directory

The user's data lives in `~/Documents/job-search/` (or whatever path is in `~/.claude/settings.json` under `jobSearchOs.userDataPath`). Resolve every file path relative to that directory.

Expected files:
- `profile.yaml` — who the user is, what they want, what they avoid
- `target-companies.md` — tiered company list from deep research
- `sources.yaml` — which sources are enabled and how
- `tracker.xlsx` — the Excel tracker
- `cover-letters.docx` — cover letters + LinkedIn outreach
- `cv/cv.pdf` or `cv/cv_sharpened.docx` — the CV (read-only; used for context)
- `logs/` — where run logs, skipped jobs, and false-positive learnings go

Python: the system `python3`. The plugin installs `python-jobspy`, `openpyxl`, `python-docx`, and `pandas` during setup.

Plugin directory (for scripts and adapters):
- `adapters/verify_url.py` + `adapters/verify_url.js` — live-URL verifier
- `adapters/finn.py`, `adapters/linkedin.py`, `adapters/jobspy_boards.py`, `adapters/careers_page.py`
- `templates/tracker_schema.py` — (re)creates a tracker if missing

## Step 1: Load profile and tracker

1. Parse `profile.yaml`. Extract: target_titles, target_locations, seniority_level, target_domains, hard_filters, min_seniority, voice_snippet.
2. Parse `target-companies.md`. Extract the company name, tier, and careers URL for each row. Group by tier.
3. Parse `sources.yaml`. Note which sources are `enabled: true` and what their `method` and `priority` are.
4. Open `tracker.xlsx` with openpyxl. Sheets: `Jobs`, `Archive`.
5. Build `seen_keys`: set of `(company.lower().strip(), title.lower().strip())` from both sheets.
6. Find the current max ID across both sheets.
7. Move any row in `Jobs` with `Status` in {"Applied", "Will not apply", "Not a real job"} → `Archive`.
8. Build `false_positives`: dict keyed by `company_lower` from Archive rows where Status = "Not a real job". For each, print a brief reflection on what likely went wrong (stale web cache, career-page not updated, etc.).

If `tracker.xlsx` doesn't exist, create it from `templates/tracker_schema.py` before step 4.

## Step 2: Multi-source search

Run each enabled source in priority order. Each adapter returns a list of candidate dicts: `{title, company, location, url, date_posted, description, source}`.

### Finn.no (method: playwright)

Run `adapters/finn.py` with the user's `target_titles` and `target_locations` (filter to Norwegian locations). It uses Playwright MCP to search `https://www.finn.no/job/fulltime/search.html`, paginates through results, and extracts each listing's direct `https://www.finn.no/job/ad/...` URL.

Always include Norwegian-language variants of target titles when the user's location list contains Norway — the adapter translates common titles automatically.

Filter out staffing agencies (Academic Work, ManpowerGroup, Experis, Adecco, Randstad, Xtra personell, and similar) at the adapter level.

### LinkedIn (method: chrome)

LinkedIn requires the user's logged-in Chrome session via the `claude-in-chrome` extension. Check that `mcp__Claude_in_Chrome__navigate` is available. If not: skip LinkedIn silently, note in the summary that LinkedIn was skipped because the extension is unavailable.

If available: run `adapters/linkedin.py`. It navigates to LinkedIn's job search via the extension, runs each target title × location query, extracts title/company/location/URL from the result cards, and returns the list.

Do NOT try to log the user in. If they aren't logged in, the adapter returns empty and notes it.

### Indeed + Glassdoor (method: jobspy)

Run `adapters/jobspy_boards.py`. It uses `python-jobspy` to scrape Indeed and Glassdoor with the user's target titles and locations. The `country_indeed` parameter comes from `sources.yaml`.

JobSpy is best-effort — it gets blocked sometimes. Catch exceptions per site/term/location combo and continue. Cap total JobSpy runtime at 10 minutes via subprocess timeout.

### Target-company career pages (method: playwright, targeted)

For Tier 1 companies from `target-companies.md`, navigate to each careers URL with Playwright MCP and look for roles matching the user's target titles and seniority.

Use `adapters/careers_page.py` helpers:
- `detect_ats_family(url)` — returns known ATS family (Greenhouse, Lever, Ashby, Workday, Teamtailor, BambooHR, SmartRecruiters, etc.) with suggested title selectors.
- `title_matches_any(page_title, target_titles)` — fuzzy title match.
- `is_above_seniority(title, min_seniority)` — seniority heuristic.
- `is_empty_state(body_text)` — detects "no open positions" pages so they don't count as errors.

Process all of Tier 1; then Tier 2 if time permits; then Tier 3 if time permits.

**Runtime budget**: total search runtime capped at 25 minutes. If Finn + LinkedIn + JobSpy together take more than 20 minutes, limit career pages to Tier 1 only and note the skipped tiers in the summary.

## Step 3: Deduplicate and hard-filter

1. Merge all candidate lists.
2. Deduplicate on `(company.lower().strip(), title.lower().strip())` — prefer the career-page URL as `Source` when a job is found on both LinkedIn/Indeed and the company page.
3. Filter out anything already in `seen_keys`.
4. Apply `hard_filters` from `profile.yaml` against title + description: reject if any filter word appears.
5. Apply `min_seniority`: if `reject_titles_below: true`, reject titles clearly below the user's level (e.g., "Senior Product Manager", "Product Owner", "Associate PM" when min_seniority is "director").
6. Apply location rules from `profile.yaml`:
   - If user's `target_locations` includes "Remote, Europe" or similar, include remote-EU roles freely.
   - Exclude on-site roles outside the user's listed locations.
   - For hybrid roles in cities not in the user's list: include only if the company appears in `target-companies.md`, else exclude.

Log per-source counts (raw hits, survived hard filters, new vs. existing) for the summary.

## Step 4: Live-URL verification (mandatory, batched)

For every remaining candidate, run `adapters/verify_url.py` in parallel (asyncio or multiprocessing, up to 8 concurrent):

```
python3 adapters/verify_url.py <url> --title <title> --company <company> \
    --learnings-file <user_dir>/logs/false_positive_learnings.json
```

Exit codes: `0 = live`, `1 = dead`, `2 = unverified`.

**Only `live` candidates proceed.** `dead` and `unverified` are both skipped. Log them to `<user_dir>/logs/skipped_jobs-<YYYY-MM-DD>.json` with company, title, URL, reason, and evidence.

If a candidate's company appears in `false_positives`, the verifier auto-escalates to high-risk host checks — no extra action needed.

## Step 5: Assess fit

For each verified-live candidate, rate fit:

- **Strong**: matches all three — seniority, domain, location — AND the role context matches the profile (company stage, direction).
- **Moderate**: partial match — interesting company or domain but one criterion is a stretch (off-title, location push, unclear growth stage). Surface for user judgment; do not auto-skip.
- **Poor**: fails hard filters → already removed in Step 3; don't reassess here.

Set `Recommendation` to "Apply Now", "Consider", or "Skip".

`Key Notes`: 2-3 short bullets explaining the fit (why it's good, any concerns). Always start with `✅ Verified live <YYYY-MM-DD HH:MM>`.

## Step 6: Draft cover letters and LinkedIn outreach (Strong fits only)

For each new Strong fit, generate:

1. A 150-180 word cover letter following the 3-move structure in `templates/cover_letter_voice.md`. Use `voice_snippet` from `profile.yaml` as a style anchor.
2. A 3-4 sentence LinkedIn outreach draft targeting a likely hiring manager / CPO / product director at the company. If no specific name is identifiable from context, use `[Name]` and add a note "Find: <role> on LinkedIn before sending."

Both go into `cover-letters.docx` under a heading `"[Company] - [Job Title]"` with a `Tracker ID:` line, then the letter, then a subheading `"[Company] — LinkedIn Outreach Draft"` with the note.

## Step 7: Write tracker rows

For each new verified-live candidate:

```python
row = [
    new_id,
    date_today,
    job_title,
    company,
    location,
    source_url,                           # always a full URL
    fit_rating,                           # "Strong" or "Moderate"
    recommendation,                       # "Apply Now" / "Consider"
    key_notes,                            # must start with "✅ Verified live ..."
    cover_text if fit == "Strong" else "",
    "",                                   # Apply By — user fills
    "New",
]
```

**Pre-save assertion**: every appended row MUST have `Key Notes` starting with `✅ Verified live `. If any row fails this check, abort the save.

Make the Source cell a clickable hyperlink (openpyxl `Font(color="0563C1", underline="single")`).

Save `tracker.xlsx` and `cover-letters.docx`.

## Step 8: Update false-positive learnings

If any row was marked `Not a real job` in this run's Archive move (Step 1.7), append an entry to `<user_dir>/logs/false_positive_learnings.json`:

```json
{
  "date_marked": "YYYY-MM-DD",
  "company": "...",
  "title": "...",
  "url": "...",
  "host": "...",
  "host_family": "...",
  "failure_mode": "..."
}
```

Bump the corresponding `host_family_counts` entry.

## Step 9: Print summary

Structured summary (keep it concise but complete):

### Search Coverage
- Per-source: raw hits, survived hard filters, new vs existing.
- Flag any source that returned zero results.
- Flag any target-company tier skipped due to runtime budget.

### New Jobs Found
- Total with Strong / Moderate breakdown.
- Table: Company | Title | Location | Fit Rating | Source URL.

### Jobs Removed (archived)
- List: company, title, status (Applied / Will not apply / Not a real job).

### False-Positive Lessons
- For each Archive row marked "Not a real job" this run: brief post-mortem (what was found, source, likely cause, rule for next time).

### Cover Letters Written
- List Strong fits with cover letter + LinkedIn outreach status.

### Tracker Status
- Total active jobs.
- Deadlines in next 7 days.

### Issues
- Any source failures, Chrome extension not present, JobSpy blocks, career pages unreachable.
- Runtime breakdown (Phase 1 / 2 / 3 / 4 elapsed).

Write the full summary to `<user_dir>/logs/run-<YYYY-MM-DD>.log` as well.

## Failure modes — what to do silently

- LinkedIn unavailable → skip, note in summary.
- JobSpy blocked on a site → skip that site, continue.
- Finn times out → retry once, then skip remaining Finn queries.
- Career page returns error or no results → note and continue.
- Runtime budget exceeded → stop the current phase, run Step 3+ on whatever was collected.
- `tracker.xlsx` locked by Excel → fail with a clear message; tell the user to close Excel and re-run.

## Failure modes — when to stop and surface

- `profile.yaml` missing or empty → stop; suggest `/job-search-setup`.
- `target-companies.md` missing → stop; suggest running `/job-search` which routes through onboarding.
- No sources enabled → stop; suggest editing `sources.yaml` or re-running setup.
- Python dependencies missing → run `scripts/install_deps.sh` once (no need to ask), retry.

Never ask the user "should I continue?" mid-run. Either complete, or stop with a clear message and a concrete next command.
