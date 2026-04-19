# Deep-research prompt (for Claude.ai, not Claude Code)

The onboarding wizard fills in this template with values from your `profile.yaml` and gives you the final prompt to paste into Claude.ai.

## Instructions for you (the user)

1. Open https://claude.ai in your browser.
2. Start a new chat.
3. Click the "Research" toggle at the bottom of the input (it turns on Claude's deep-research mode).
4. Paste the prompt below.
5. Wait a few minutes for Claude to research.
6. Copy the final list from Claude's response.
7. Save it as `target-companies.md` in your job-search folder.
8. Go back to Claude Code and type `/job-search` — it picks up from there.

---

## The prompt (the wizard fills in the `{{...}}` values)

```
I'm researching companies to target for my next job.

My profile:
- Target title(s): {{target_titles}}
- Seniority level: {{seniority_level}}
- Location(s) I'll accept: {{target_locations}}
- Domains I'm interested in: {{target_domains}}
- Company stages I'm open to: {{company_stage}}
- Things I want to AVOID: {{hard_filters}}

Please research and produce a list of 40–60 companies that match my profile.

For each company, give me:
- Name
- Headquarters / primary location
- Stage (seed / Series A / B / C-D / public / private)
- Why they're a fit for me (1–2 sentences)
- Careers page URL (direct link, not a redirect)

Group them into tiers:
- **Tier 1 (Top targets)**: companies where I'd ideally want to work right now. Strong match on every dimension.
- **Tier 2 (Strong)**: solid fit, worth tracking.
- **Tier 3 (Stretch / Interesting)**: off-profile in one dimension but still worth watching.

Prioritize companies that currently have, or are likely to soon have, open roles at my level.

At the end, give me the list in this exact Markdown format so I can save it as a file:

---

# Target Companies

## Tier 1

| Company | Location | Stage | Why fit | Careers URL |
|---|---|---|---|---|
| ... | ... | ... | ... | https://... |

## Tier 2

| Company | Location | Stage | Why fit | Careers URL |
|---|---|---|---|---|
| ... | ... | ... | ... | https://... |

## Tier 3

| Company | Location | Stage | Why fit | Careers URL |
|---|---|---|---|---|
| ... | ... | ... | ... | https://... |

---

Research carefully. Use multiple sources. Verify careers URLs are real and currently reachable.
```
