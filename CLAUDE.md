# Job Search OS — Operating Rules

These rules apply to EVERY skill and command in this plugin. They exist to keep the experience usable for non-technical users. Follow them strictly.

## 1. Don't ask the user about plumbing

The user is here to find a job, not to configure software. Never ask them to choose between technical options. Decide for them using the plugin's documented defaults and proceed.

- ❌ "Should I use python-jobspy or Playwright for this search?" → use the source's documented adapter.
- ❌ "Which browser should I use?" → Playwright MCP for Finn, Chrome MCP for LinkedIn. Non-negotiable.
- ❌ "Do I have permission to write this file?" → the plugin's permissions template pre-approves all writes inside `~/Documents/job-search/`. If a write fails, fix it, don't ask.
- ❌ "Should I install the dependency?" → if it's in `scripts/install_deps.sh`, install it without asking.

## 2. Don't ask "should I continue?" mid-recipe

Every skill is a recipe with deterministic steps. Run the whole recipe. Report at the end.

- ❌ "I've loaded the tracker. Should I proceed to search?"
- ✅ Run: load tracker → search → assess → write cover letters → update files → summary. Report once.

The exception: if an irrecoverable error occurs (e.g., Chrome MCP is not installed and LinkedIn is requested), stop, explain, and offer concrete next steps.

## 3. Interrupt ONLY for real user decisions

Real decisions are things only the user knows:
- Their target job titles, locations, and seniority
- Which companies they want to target
- Whether a specific job is a good fit (when the plugin flags it as ambiguous)
- Whether to apply, skip, or mark a job as "not real"
- Voice snippets for cover letters

Everything else → the plugin decides.

## 4. Batch questions, don't drip them

When the onboarding wizard needs input, use `AskUserQuestion` with all 4 questions at once. One batch is one interruption. Four one-question batches is four interruptions — bad experience.

Target for first-time setup: ≤ 4 AskUserQuestion batches total.

## 5. Fail silently to the next fallback, surface only when exhausted

When a source fails (e.g., JobSpy gets blocked on Indeed), try the documented fallback silently, keep going, and mention it in the final summary. Never interrupt the user to say "Indeed failed, should I try again?" — just skip it and note it.

## 6. Never invent user data

If a field is missing (no CV, no profile, no target list), run the relevant onboarding step to collect it. Do NOT make up a job title, seniority, or target companies.

## 7. Verification contract

URL-sourced rows (from daily search, or a URL supplied to `/job-search-add`) MUST be verified live by `adapters/verify_url.py` returning `live`. Their `Key Notes` starts with `✅ Verified live <YYYY-MM-DD HH:MM>`.

Manually-added rows with no URL (paste or screenshot via `/job-search-add`) cannot be verified — there's nothing to check. Their `Key Notes` starts with `⚠️ Unverified manual entry — confirm this job exists before applying.` and `Source` is `"Manual"`.

These are the only two prefixes allowed. If a row's `Key Notes` starts with neither, the skill has a bug and the row must not be written.

## 8. Default working directory

All user data lives in the folder recorded in `~/.claude/settings.json` under `jobSearchOs.userDataPath` (default: `~/Documents/job-search/`). Resolve paths against that directory. Never write outside it.

## 9. Personal-data guard

This plugin is public. Skill outputs (cover letters, tracker entries, summaries) must only contain the installing user's own data — their name, their CV, their profile, their target companies. Never leak the plugin author's personal details or anyone else's data into a user's outputs.

## 10. If the user is stuck, show `/job-search-status`

When something isn't working, don't guess — run the diagnose skill and show the user a structured state report. It tells them exactly what's set up and what's missing.
