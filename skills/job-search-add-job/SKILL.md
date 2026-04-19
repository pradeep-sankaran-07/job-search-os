---
name: job-search-add-job
description: Add a single job to the tracker manually. Accepts a URL, pasted text, or a screenshot image. Verifies the posting is live, applies profile filters, rates fit, writes a cover letter for Strong fits, and adds the row to tracker.xlsx. Runs end-to-end without asking for confirmation.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(python3:*)
  - Bash(node:*)
  - WebFetch
---

You are adding one job to the user's tracker. Run the full recipe — do NOT pause mid-way.

## Intent

Give the user a consistent entry point for a job they found outside the daily search (a friend's tip, a screenshot, a direct URL). The tracker must end up with a row that looks identical to a daily-run row, with the same trust guarantees (URL-sourced → verified live; no URL → marked ⚠️ Unverified manual entry). Don't invent verification. Don't lose the role silently.

## Python binary resolution

Windows users don't have `python3` on PATH. Before running any Python command, resolve the binary:
1. Read `<user_dir>/.python-bin` if it exists (the install script writes it).
2. Otherwise probe: `python3` → `python` → `py -3`. Use the first that works.
3. Refer to the resolved binary as `<python>` throughout this skill.

## Working directory

User's data: `~/Documents/job-search/` (or whatever is set in `~/.claude/settings.json` under `jobSearchOs.userDataPath`).

Key files:
- `profile.yaml` — target titles, locations, hard filters, seniority
- `tracker.xlsx` — where the new row goes
- `cover-letters.docx` — where the cover letter goes (Strong fits only)

## Input forms

The user provides one of:
- A **URL** (typed or pasted into the command).
- **Pasted text** — a copy of the job description.
- A **screenshot image** — dropped into chat.

## Step 1: Extract job details

**If URL**: WebFetch the URL. Extract title, company, location, and description.

**If pasted text**: parse for title, company, location, description.

**If screenshot**: use vision to extract title, company, location, and description.

If any of {title, company, location} cannot be extracted, ask the user for just that one missing field (do not re-ask for things you already have). Then continue.

## Step 2: Load tracker and filter

1. Open `tracker.xlsx`. Sheets: `Jobs`, `Archive`.
2. Build `seen_keys` (set of `(company.lower().strip(), title.lower().strip())`) from BOTH sheets.
3. Compute `max_id`: the maximum integer value in column A across both sheets, default 0 if empty.
4. Move any row in `Jobs` with `Status` in {"Applied", "Will not apply", "Not a real job"} → `Archive` (standard maintenance).
5. Apply `hard_filters` from `profile.yaml`. If rejected, stop and tell the user which filter matched. Do not add the row.
6. Apply `min_seniority`. If below, stop and explain.
7. Apply location rules. If the role is outside the user's listed locations and not remote/hybrid-in-Oslo-equivalent, stop and explain.
8. Check `seen_keys`. If the `(company, title)` pair is already in the tracker or Archive, stop and tell the user "Already tracked."

## Step 3: Verify live (if URL provided)

If a URL was provided, run `adapters/verify_url.py`:

```bash
python3 <plugin_dir>/adapters/verify_url.py "<url>" \
    --title "<title>" --company "<company>" \
    --learnings-file <user_dir>/logs/false_positive_learnings.json
```

- Exit code `0` (live): proceed.
- Exit code `1` (dead) or `2` (unverified): stop. Tell the user: `"Verifier says this posting is <status>: <reason>. Evidence: <bodySample>. Not adding to tracker."` Do not add, do not add with a caveat.

If the user provided pasted text or a screenshot (no URL), set `Source = "Manual"` and skip verification — there's nothing to verify. Warn the user in the summary that the row is unverified.

## Step 4: Rate fit

- **Strong**: right seniority + right domain + right location. Proceed to add to tracker + write cover letter.
- **Moderate**: partial match. Proceed to add to tracker; leave Cover Letter Text blank.
- **Weak**: should not happen (Step 2 removed these). If it does, stop and explain.

## Step 5: Write row

Columns: `ID | Date Found | Job Title | Company | Location | Source | Fit Rating | Recommendation | Key Notes | Cover Letter Text | Apply By | Status`

```python
from openpyxl.styles import Alignment, Font
from datetime import date, datetime

new_id = max_id + 1
source_value = url if url and url.startswith("http") else "Manual"
verified_prefix = (
    f"✅ Verified live {datetime.now().strftime('%Y-%m-%d %H:%M')}" if url
    else "⚠️ Unverified manual entry — confirm this job exists before applying."
)
key_notes = f"{verified_prefix}\n" + "\n".join(fit_bullets)

row_data = [
    new_id,
    date.today().strftime("%Y-%m-%d"),
    job_title,
    company,
    location,
    source_value,
    fit_rating,
    recommendation,
    key_notes,
    cover_text if fit_rating == "Strong" else "",
    "",
    "New",
]
ws_jobs.append(row_data)

# Make Source a clickable hyperlink.
if source_value.startswith("http"):
    src_cell = ws_jobs.cell(row=ws_jobs.max_row, column=6)
    src_cell.hyperlink = source_value
    src_cell.value = source_value
    src_cell.font = Font(color="0563C1", underline="single")

wb.save("tracker.xlsx")
```

**Pre-save assertion**: `key_notes.startswith("✅ Verified live ")` for URL-sourced rows, OR `key_notes.startswith("⚠️ Unverified manual entry")` for paste/screenshot rows. Any other prefix = bug, abort the save.

## Step 6: Cover letter (Strong fits only)

Use the structure in `<plugin_dir>/templates/cover_letter_voice.md`. Apply the user's `voice_snippet` from `profile.yaml` as a style anchor.

Append to `cover-letters.docx` with heading `"[Company] - [Job Title]"`, a `Tracker ID: #X` line, a contact block from `profile.yaml`, the letter, and a LinkedIn outreach draft.

## Step 7: Summary

```
=== JOB ADDED ===
ID: #X | <Title> at <Company> | <Location>
Source: <URL or Manual>
Fit: <Strong / Moderate> | Cover letter: <Yes / No>
Key notes: <2-3 lines>
```

## Don't interrupt the user

- Don't ask "should I add this?" — the user asked you to add it; add it.
- Don't ask "how should I handle the filter mismatch?" — tell them it mismatched and stop.
- Don't ask "should I write a cover letter?" — Strong fits get one, Moderate fits don't. No discussion.
