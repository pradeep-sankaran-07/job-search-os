# Job Search OS

A guided, automated job-search workflow that lives inside Claude Code. Built for non-technical users — install it once, answer a few questions, and every morning it searches LinkedIn, Finn.no, Indeed, and Glassdoor, writes first-draft cover letters, and updates an Excel tracker.

Default search region: **Norway + Nordics + Remote Europe** (the Finn.no adapter is Norway-specific; the other sources are region-agnostic).

**Platform support:** macOS, Linux, and Windows. The setup wizard detects your OS and runs the right installer automatically — no user intervention needed.

**One-page setup guide**: [docs/Job-Search-OS-Setup-Guide.pdf](docs/Job-Search-OS-Setup-Guide.pdf) — share this with friends who want to install it.

---

## Install (one command, if you're a user)

```
/plugin marketplace add pradeep-sankaran-07/job-search-os
/plugin install job-search-os
/job-search-setup
```

The rest is guided. No GitHub account needed. Full walkthrough: [HOW_TO_USE.md](HOW_TO_USE.md).

**Requirements**: Claude Pro or Max subscription · Claude Desktop · Chrome + the `claude-in-chrome` extension (for LinkedIn).

---

## What it does

1. **Onboarding** — drop your CV, answer 10 questions, get a profile.
2. **Target-companies research** — one-time handoff to Claude.ai's Research mode; paste the result back.
3. **Daily search** — runs across Finn.no (Playwright), LinkedIn (Chrome), Indeed + Glassdoor (JobSpy).
4. **Live-URL verification** — every tracker row is confirmed live in a real browser before it's written. No ghost listings.
5. **Cover letters** — first-draft cover letter + LinkedIn outreach message for every Strong-fit role.
6. **Tracker** — `tracker.xlsx` with Jobs and Archive tabs, status dropdowns, auto-archive on `Applied` / `Will not apply`.

---

## Slash commands

| Command | What it does |
|---|---|
| `/job-search` | Main entry. Diagnoses state and runs the next needed step. |
| `/job-search-setup` | First-time wizard. Sets up folder, profile, sources, schedule. |
| `/job-search-status` | Reports what's set up vs missing. Troubleshooting. |
| `/job-search-daily` | Runs today's search now. |
| `/job-search-add <url or paste>` | Add a single job manually from URL, text, or screenshot. |
| `/job-search-add-source <name>` | Enable a new job-board source. |

---

## Repo layout

```
CLAUDE.md                      quiet-operation rules loaded into every session
.claude-plugin/
  plugin.json                  plugin manifest
  marketplace.json             marketplace manifest (makes the one-line install work)
  settings.template.json       pre-approved permissions, merged at setup
commands/                      slash commands
skills/
  job-search-onboarding/       CV → profile → targets → schedule wizard
  job-search-daily/            the multi-source daily run
  job-search-add-job/          manual entry (URL/text/screenshot)
  job-search-diagnose/         state checker
  job-search-add-source/       add a new board
adapters/
  finn.py                      Finn.no via Playwright MCP
  linkedin.py                  LinkedIn via Chrome MCP (logged-in session)
  jobspy_boards.py             Indeed + Glassdoor via python-jobspy
  careers_page.py              generic career-page scraper
  verify_url.py                live-URL verifier (Playwright, headless)
templates/                     profile.yaml, cover_letter_voice.md, etc.
scripts/
  install_deps.sh              one-line dependency install
HOW_TO_USE.md                  non-technical user guide
ROADMAP.md                     v0.2 plans (source auto-detect cascade)
```

---

## Privacy

All user data stays in `~/Documents/job-search/` on the user's local machine. The plugin makes search-engine calls to Finn/LinkedIn/Indeed/Glassdoor (the same kind of call you'd make typing into those sites) and sends prompts to Claude per normal. It does not phone home and has no analytics.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Credits

Built by [Pradeep Sankaran](https://github.com/pradeep-sankaran-07) — forked and generalized from a personal job-search automation he uses every day.
