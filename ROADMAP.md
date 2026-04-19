# Roadmap

## v0.1 (current)

Ships with four sources, hand-crafted:

- **Finn.no** — Playwright MCP (headless)
- **LinkedIn** — Chrome MCP (user's logged-in session)
- **Indeed** — python-jobspy (best-effort)
- **Glassdoor** — python-jobspy (best-effort)

`/job-search-add-source` accepts only these four names. Anything else is routed to manual entry via `/job-search-add`.

Intended audience: a non-technical user who wants something that works on day 1 for Norway + Nordics + Remote Europe searches.

---

## v0.2 (planned) — source auto-detect cascade

The original design goal: when the user asks to add any new job board (e.g. Welcome to the Jungle, StepStone, Honeypot, Otta, Wellfound), the plugin figures out the best way to search it.

Cascade (try each in order, use the first that succeeds):

1. **Direct library** — does `python-jobspy` or another maintained Python adapter support this source? Test with a sample query for the user's primary target title. If it returns structured results with URL, title, company, and location, register it with `method: library`.

2. **Simple HTTP + parser** — does the site expose a public JSON API, RSS feed, or a static-HTML search page? Fetch the HTML, look for schema.org JobPosting markup or a predictable list structure. If parseable, register with `method: http`.

3. **Playwright MCP** — navigate the search page with headless Chromium. Does the DOM have a clear listing structure? If yes and the page loads without a login wall, register with `method: playwright`.

4. **Chrome MCP** — fall back to the user's logged-in Chrome session if the site requires auth (like LinkedIn). Register with `method: chrome`.

5. **Flag as unsupported** — if all four fail, tell the user the source can't be automated and suggest manual entry.

### Success criteria per step

| Step | Success criterion |
|---|---|
| 1 | Returns ≥ 1 row with title, company, url for a test query |
| 2 | HTML contains ≥ 3 listings with structured fields |
| 3 | Playwright snapshot finds a repeating card pattern with text matching target titles |
| 4 | Chrome navigates logged-in and finds same pattern |

### Metadata stored per source

`sources.yaml` entry after auto-detect:
```yaml
welcometothejungle.com:
  enabled: true
  method: playwright
  detected_at: 2026-05-01
  last_verified: 2026-05-01
  last_success_rate: 1.0     # updated after each run
  search_url_template: "https://www.welcometothejungle.com/en/jobs?query={query}&region={location}"
  card_selector: "[data-testid='job-card']"
  fields:
    title: "[data-testid='job-title']"
    company: "[data-testid='company-name']"
    location: "[data-testid='location']"
    url: "a[href]"
```

### Re-verification

Once a month, on the scheduled daily run, re-test each source's extraction. If success rate drops below 50%, flag it in the status report and offer to re-run auto-detect.

---

## v0.3 and beyond

- **Cowork integration** — for users who already use Cowork, offer a `job-search-review` skill that runs weekly summaries across the tracker and helps decide where to focus next week.
- **Non-English job boards** — generalise the Norwegian-translation layer in `adapters/finn.py` to pluggable locale maps (German: `adapters/stepstone.py` template; Spanish: `adapters/infojobs.py`; etc.).
- **Automated application drafting** (not submission) — for ATS-supported sites where we have the JD, pre-fill answers to common screening questions from the user's profile, then hand off to the user to review and submit.
- **Hosted web UI** — a simple read-only web view of the tracker that the user can open alongside Claude Code. Likely not a priority; Excel already works.

---

## What's explicitly not planned

- **Autonomous apply-and-send** — the user always clicks Apply. We don't automate the submission.
- **Fake or generated CVs** — we only read, analyse, and suggest edits to the user's real CV. No AI-generated resume spam.
- **Multi-user / team features** — this is a personal tool. If the team use case is strong, it would likely be a different product.
