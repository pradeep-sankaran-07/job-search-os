---
name: job-search-add-source
description: Enable a new job-board source for daily searches. In v0.1 supports Finn, LinkedIn, Indeed, Glassdoor. For anything else, explains v0.1 limits and suggests manual entry or waiting for v0.2's auto-detect cascade.
allowed-tools:
  - Read
  - Edit
  - Write
---

You are enabling a job-board source in the user's `sources.yaml`. In v0.1 this is a simple lookup; the auto-detect cascade (library → HTTP → Playwright → Chrome MCP) is planned for v0.2 (see ROADMAP.md).

## Supported sources in v0.1

| Input names (any of these) | Adapter | Method |
|---|---|---|
| `finn`, `finn.no`, `www.finn.no` | `adapters/finn.py` | Playwright MCP |
| `linkedin`, `linkedin.com` | `adapters/linkedin.py` | Chrome MCP (requires extension) |
| `indeed`, `indeed.com` | `adapters/jobspy_boards.py` | python-jobspy |
| `glassdoor`, `glassdoor.com` | `adapters/jobspy_boards.py` | python-jobspy |

## Step 1: Parse input

Normalize the user's input (strip protocol, lowercase, strip `www.`). Match against the table above.

## Step 2a: If matched

- Open `<user_dir>/sources.yaml`.
- If the source entry exists: set `enabled: true`.
- If the source entry doesn't exist (shouldn't happen — setup writes all four): add it with defaults from `<plugin_dir>/templates/sources.yaml`.
- For LinkedIn specifically: first verify that `mcp__Claude_in_Chrome__navigate` is available. If not, tell the user to install the extension and don't enable it.
- Save `sources.yaml`.

Report:
```
✅ <Source> enabled. It will run in your next daily search.
```

## Step 2b: If not matched

Do NOT attempt to build an adapter on the fly. Tell the user:

```
"<input>" is not supported in v0.1 of Job Search OS.

v0.1 supports: Finn.no, LinkedIn, Indeed, Glassdoor.

Two options:
  1. Track jobs from this source manually:
       /job-search-add <URL>
     Works for any site with a direct job URL.

  2. Watch for v0.2, which will include an auto-detect cascade
     (tries a direct library, then a simple scraper, then Playwright,
     then Chrome MCP) for arbitrary boards.

See <plugin_dir>/ROADMAP.md for details.
```

## Step 3: Disabling a source

If the user invokes `/job-search-add-source <name> --disable` (or says "disable linkedin"):

- Set `enabled: false` on that entry.
- Save.
- Report: `"⚠️  <Source> disabled. It won't run in daily searches. Re-enable with /job-search-add-source <name>."`

## Don't

- Don't try to write a new adapter for an unknown source. That's v0.2 territory.
- Don't ask the user to configure anything beyond enable/disable. The adapter handles everything else.
