---
description: Add a single job to your tracker. Accepts a URL, pasted text, or a screenshot.
argument-hint: [URL or paste text]
---

The user wants to add one job. The argument may be:
- A URL (starts with http)
- Pasted job description text
- Empty (user will drop a screenshot into chat next)

Invoke the `job-search-add-job` skill. Pass whatever the user provided. If the argument is empty, wait for a screenshot or paste in the next message before calling the skill.

The skill handles everything: extraction, filtering, live-URL verification, fit rating, writing the row, and drafting a cover letter for Strong fits.
