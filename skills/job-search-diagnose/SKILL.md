---
name: job-search-diagnose
description: Diagnose the state of the user's Job Search OS setup. Reports what's configured, what's missing, what's stale, and offers concrete one-command fixes. Used as both a standalone /job-search-status command and as the router in /job-search to decide the next step.
allowed-tools:
  - Read
  - Bash(ls:*)
  - Bash(python3:*)
  - Bash(python:*)
  - Bash(py:*)
  - Bash(pip:*)
  - Bash(pip3:*)
  - Bash(claude:*)
  - Bash(grep:*)
  - Bash(where:*)
  - Bash(which:*)
---

You are reporting the user's setup state. Be concise, structured, and actionable. The user should be able to see the whole state at a glance and know exactly what to do next.

## Intent

Give the user (and the router in `/job-search`) a precise reading of what's set up and what's missing, so they can run one concrete command to fix whatever's broken. Do not try to fix things here — diagnose only. The fix-it table at the bottom of this skill tells them which command to run.

## Python binary resolution

See CLAUDE.md §11. When probing for python packages, read `<user_dir>/.python-bin` first; fall back to `python3` → `python` → `py -3`.

## Working directory

User's data: `~/Documents/job-search/` (or whatever is set in `~/.claude/settings.json` under `jobSearchOs.userDataPath`).

## Checks to run

Run all of these; include each in the report.

### 1. Installation

- Plugin installed? (check existence of `<plugin_dir>/.claude-plugin/plugin.json`)
- User-data path set in settings? (`jobSearchOs.userDataPath`)
- User-data folder exists?
- Permissions merged? (look for any `mcp__playwright__*` entry in user's settings.json → proxy for "merge happened")

### 2. Python + MCP dependencies

Test-import each, report version if present:
- `python-jobspy` (via `pip show python-jobspy`)
- `openpyxl`
- `python-docx`
- `pandas`
- `pyyaml`

Check MCP servers (the `grep` invocation below works on macOS/Linux; on Windows, run `claude mcp list` and scan the output for "playwright"):
- Playwright MCP: `claude mcp list` → look for `playwright`
- Claude-in-Chrome MCP: is `mcp__Claude_in_Chrome__navigate` tool available?

### 3. User files

For each, report present/missing and last-modified:
- `profile.yaml` → valid YAML? all required fields filled? (required: target_titles, seniority_level, target_locations)
- `cv/` → any file? which?
- target-companies file → exists? Look for any of `Target Companies.pdf`, `target-companies.pdf`, `target-companies.md`, `target-companies.txt`, `target-companies.docx` (case-insensitive). How many Tier 1/2/3 companies?
- `sources.yaml` → exists? which sources enabled?
- `tracker.xlsx` → exists? row count in Jobs, row count in Archive
- `cover-letters.docx` → exists?
- `logs/false_positive_learnings.json` → exists? host-family counts?

### 4. Schedule

- Is `job-search-daily` scheduled? (check `<user_dir>/.schedule.yaml` if the setup skill wrote one)
- Next run time?
- Last successful run? (check `<user_dir>/logs/run-*.log` modification time)

### 5. Freshness

- Profile last modified > 90 days ago? Flag as potentially stale.
- target-companies file last modified > 180 days ago? Flag.
- Tracker has rows where `Status = "New"` and `Apply By` is in the past? Flag as overdue.

## Output format

Print a structured report with clear status emoji. Keep it scannable.

```
Job Search OS — Status

INSTALLATION
  Plugin:            ✅ installed (v0.1.0)
  User folder:       ✅ ~/Documents/job-search/
  Permissions:       ✅ merged

DEPENDENCIES
  python-jobspy:     ✅ 1.2.3
  openpyxl:          ✅ 3.1.2
  python-docx:       ✅ 1.1.0
  pandas:            ✅ 2.2.0
  pyyaml:            ✅ 6.0.1
  Playwright MCP:    ✅ connected
  Chrome MCP:        ⚠️  not installed — LinkedIn will be skipped

USER DATA
  profile.yaml:       ✅ complete (3 target titles, 2 locations)
  CV:                 ✅ cv.pdf (modified 2026-03-01)
  target-companies:   ✅ 52 companies (Tier 1: 10, Tier 2: 24, Tier 3: 18)
  sources.yaml:       ✅ finn, indeed, glassdoor enabled (linkedin disabled)
  tracker.xlsx:       ✅ 18 active jobs, 7 archived
  cover-letters.docx: ✅ 12 letters drafted

SCHEDULE
  Daily run:         ✅ 08:00 weekdays (next: tomorrow 08:00)
  Last successful:   2026-04-18 08:12 (26 hours ago)

WHAT TO DO NEXT
  • Install Claude-in-Chrome extension to enable LinkedIn search
    → https://chromewebstore.google.com/...
  • Run today's search: /job-search-daily
```

## When called from `/job-search` (router mode)

If invoked by the `/job-search` router command (not directly by user), return the state as a machine-readable summary AND print the human report, so the router can decide next step:

- `no_folder` → route to `/job-search-setup`
- `no_cv` → route to `/job-search-setup` step 5
- `no_profile` → route to `/job-search-setup` step 6
- `no_targets` → print deep-research handoff and wait
- `no_sources` → (should not happen; setup writes it) offer to reset
- `no_schedule` → ask "want to schedule?" (single question, not a batch)
- `ready` → ask "run today's search, add a job, or add a new source?" (single AskUserQuestion)
- `stale` → run daily anyway; flag staleness in the output

## Fix-it one-liners

For each problem, include the exact command to fix it:

| Problem | Fix |
|---|---|
| No user folder | `/job-search-setup` |
| No profile | `/job-search-setup` (resumes at profile step) |
| No target companies | Switch to Chat mode in the Claude desktop app, enable Research, paste the prompt, save the result as `Target Companies.pdf` in the job-search folder |
| Chrome MCP missing | install the Claude-in-Chrome extension |
| Playwright MCP missing | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| Python dep missing (macOS / Linux) | `bash <plugin_dir>/scripts/install_deps.sh` |
| Python dep missing (Windows) | `powershell -ExecutionPolicy Bypass -File <plugin_dir>\scripts\install_deps.ps1` |
| Tracker corrupted | `python3 <plugin_dir>/templates/tracker_schema.py <user_dir>/tracker.xlsx` (will overwrite — warn first) |
| Last run > 3 days ago | `/job-search-daily` to catch up |

## Don't

- Don't fix anything automatically without telling the user. Diagnose and suggest; the user runs the fix command.
- Don't ask questions. This is a read-only report.
- Don't be chatty. Report, suggest, done.
