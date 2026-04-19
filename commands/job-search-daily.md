---
description: Run today's multi-source job search now. Searches Finn, LinkedIn, Indeed, Glassdoor, updates your tracker, writes cover letters for Strong fits.
---

Invoke the `job-search-daily` skill. The skill runs end-to-end without pausing — it only reports at the end.

Before running, quickly verify prerequisites:
- `profile.yaml`, `sources.yaml`, `tracker.xlsx`, and a target-companies file (any of `Target Companies.pdf`, `target-companies.pdf`, `target-companies.md`, `target-companies.txt`, `target-companies.docx`) all exist in the user's job-search folder.
- At least one source in `sources.yaml` is `enabled: true`.

If any prerequisite is missing, do NOT run the daily search — invoke `job-search-diagnose` instead so the user sees what's missing and how to fix it.

Expected runtime: 15–30 minutes.
