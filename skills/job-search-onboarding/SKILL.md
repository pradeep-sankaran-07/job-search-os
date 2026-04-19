---
name: job-search-onboarding
description: First-time setup wizard for Job Search OS. Creates the user's job-search folder, installs dependencies, merges the plugin's permission allowlist, collects profile info, handles CV intake, triggers the deep-research handoff to Claude.ai, and schedules the daily run. Designed to keep interruptions to ≤ 5 question batches total.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(python3:*)
  - Bash(bash:*)
  - Bash(mkdir:*)
  - Bash(ls:*)
  - Bash(which:*)
  - Bash(npm:*)
  - Bash(npx:*)
  - Bash(claude:*)
  - AskUserQuestion
---

You are walking a non-technical user through first-time setup. Be decisive. Batch your questions. Install things without asking. Only interrupt for real user decisions.

## Target interaction budget

- ≤ 4 `AskUserQuestion` batches (max 4 questions each → 16 questions total).
- ≤ 3 permission prompts from the user.

If the run exceeds these, something is wrong — shorten the wizard before shipping.

## Step 1: Detect existing state

Check for:
- `~/.claude/settings.json` → has `jobSearchOs.userDataPath`? If yes, this is a re-run.
- User data folder exists? What's in it?
- `tracker.xlsx` present? `profile.yaml` present? `target-companies.md` present?
- Schedule for `job-search-daily` already registered?

Print a one-line state summary: `"Found existing setup at <path>. Profile: <complete/incomplete>. Tracker: <rows>. Schedule: <on/off>."` and jump to whatever step is missing. No "starting from scratch" for re-runs.

## Step 2: Pick folder and merge settings (batch 1 — at most 2 questions)

Ask the user (batch 1):
1. "Where should your job-search folder live?" (options: default `~/Documents/job-search/`, different path)
2. "May I merge the plugin's permission allowlist into your Claude settings?" (options: Yes — reduces future permission prompts / No — I'll approve each prompt myself)

Then:
- Create the folder structure:
  ```
  <user_dir>/
  ├── cv/
  ├── logs/
  └── (files populated later)
  ```
- If yes to permissions merge: read `<plugin_dir>/.claude-plugin/settings.template.json` and merge its `permissions.allow` list into `~/.claude/settings.json`. Keep the user's existing entries. Add `jobSearchOs.userDataPath` pointing to their folder.
- Write `sources.yaml` from `<plugin_dir>/templates/sources.yaml`. **After writing, set `sources.indeed.country_code`** based on the user's primary target location (derived in Step 6 after profile Q&A — either re-save here after Q&A, or defer this write until Step 6.1). Valid jobspy country codes: `norway`, `sweden`, `denmark`, `finland`, `germany`, `france`, `netherlands`, `uk`, `usa`, `worldwide` (lowercase). If the user's primary location doesn't map to a jobspy country (e.g. "Remote, Europe"), use `"worldwide"`.

## Step 3: Install dependencies silently (auto-detect OS)

First, detect the user's OS — this is silent, no user question needed:

```bash
python3 -c "import platform; print(platform.system())"
# Prints: "Darwin" (macOS), "Linux", or "Windows"
```

Or if Python isn't available yet, use shell detection:
- `$OS` env var on Windows is `"Windows_NT"`
- `uname -s` on macOS returns `Darwin`, Linux returns `Linux`

Then run the correct installer in one shot:

**macOS / Linux:**
```bash
bash <plugin_dir>/scripts/install_deps.sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File <plugin_dir>/scripts/install_deps.ps1
```

Both scripts install the same things: Python deps (`python-jobspy openpyxl python-docx pandas pyyaml`), the Playwright MCP server, Chromium, and register the MCP with Claude Code. They handle PEP 668 (externally-managed Python) with `--user` and `--break-system-packages` fallbacks.

If any step fails, surface the error but do NOT abort — the user can retry later and some pieces (manual add, profile collection) still work without all deps.

Do not ask the user "which OS?" or "should I install?" — detect the OS silently, run the right script, move on.

**Path handling**: always use `pathlib.Path.home() / "Documents" / "job-search"` or `os.path.expanduser("~/Documents/job-search")` — both work identically on macOS, Linux, and Windows. Do not hard-code `/Users/` or `C:\Users\`.

## Step 4: Detect Chrome MCP (for LinkedIn)

Check whether `mcp__Claude_in_Chrome__navigate` is available (list MCP tools).

If yes: set `sources.yaml -> linkedin.enabled: true`, note to the user that LinkedIn is ready.

If no: keep LinkedIn disabled. Tell the user:
> "LinkedIn needs the Claude-in-Chrome extension. Install it from the Chrome Web Store (search 'Claude in Chrome'), sign in with your Claude account, and log into LinkedIn in that Chrome window. Then re-run `/job-search-setup` and I'll enable it."

Do NOT block the rest of setup on this. Proceed.

## Step 5: Drop CV + build profile (one continuous flow)

This is ONE lived experience for the user, not two separate steps. Walk through it without pausing for approval between sub-steps.

### 5a. Take the CV

Check `<user_dir>/cv/` for any file.

- **If empty**: tell the user: "Drop your CV (PDF or .docx) into `<user_dir>/cv/`, or drag it into this chat." Wait for the file to appear.
- **If a CV is already there**: read it silently, print one line — "Found `<filename>`".

Read the CV (PDFs via `python-docx` for .docx or a PDF library; fall back to OCR if needed).
Extract: name, email, phone, current/last title, location, years of experience, visible strengths (top 3), any obvious weaknesses (1-2, e.g. "no quantified outcomes", "dense paragraphs").

### 5b. Profile Q&A — two batches of four

Collect the profile via 2 batches of `AskUserQuestion`. Ask them immediately after the CV is read — no "shall we continue?" prompt in between.

**Batch 1 — the basics** (4 questions):
1. "What job titles are you targeting?" (free-text multi-select or "Other" for custom)
2. "What seniority level?" (IC / Manager / Director / VP / C-level)
3. "Where will you work?" (multi-select: Norway / Nordic / Remote Europe / Remote Global / Specific city)
4. "Should I polish your CV for you?" (Yes — save as a new file alongside the original / No — leave it as is)

**Batch 2 — preferences and filters** (4 questions):
1. "What industries / domains are you interested in?" (multi-select: B2B SaaS / AI / Fintech / Marketplace / Industrial / Healthcare / Other)
2. "What company stages are okay?" (multi-select: Seed / Series A / Series B / Series C+ / Public / Any)
3. "Any dealbreakers? What should I NEVER show you?" (multi-select: Crypto/Web3 / Hardware / Consumer goods / Staffing/Contract / Pre-sales / None)
4. "Paste 1-2 sentences of your own writing (email to a peer, a LinkedIn post, anything) — I'll use it to match your voice in cover letters. Optional — you can skip." (Other for free-text paste; empty = skip)

### 5c. CV recommendations + polish

After Batch 1 answers come back, regardless of question 4 answer, print **2-4 concrete, specific recommendations** based on the CV you read in 5a. Examples of good recommendations (adapt to the actual CV):

- "Bullet 3 under your most recent role ('led product team') is vague — replace with a quantified outcome: what shipped, what metric moved, in what timeframe?"
- "Your summary says 'results-oriented' — cut it; every CV says that. Lead with the one thing that makes your background unusual."
- "Dates on your 2019 role are missing the end month."
- "Education section has a typo: 'Universty'."

**If the user said yes to polishing** (Batch 1 Q4): apply those recommendations and save to `<user_dir>/cv/cv_polished.docx` (or `.pdf` matching the original format). Keep the original file untouched. Tell the user: "Saved the polished version as `cv_polished.docx` — original is still there."

**If the user said no**: print the recommendations as a list and tell them: "Saved these as notes — you can ask me to apply them any time: 'Please apply those CV recommendations.'"

### 5d. Write the profile

Write all Batch 1 + Batch 2 answers, plus name/email/phone/linkedin extracted from the CV, to `<user_dir>/profile.yaml`, using `<plugin_dir>/templates/profile.yaml` as the schema.

Also re-save `<user_dir>/sources.yaml` now, filling in `sources.indeed.country_code` from the user's primary target location (see Step 2 for valid values).

### 5e. Create tracker

Run:
```bash
python3 <plugin_dir>/templates/tracker_schema.py <user_dir>/tracker.xlsx
```

Also create an empty `<user_dir>/cover-letters.docx` so later skills can append cleanly.

Print a one-line summary: "CV ✅  Profile ✅  Tracker ✅  — next we'll pick your target companies."

## (Step 6 and Step 7 merged into Step 5 above)

## Step 8: Target-companies handoff — explicit, to Claude chat

Generate the deep-research prompt by reading `<plugin_dir>/templates/deep_research_prompt.md` and filling in the `{{...}}` placeholders from `profile.yaml` (which you just wrote in Step 5d).

Then print this **exact** block to the user — unmistakable sub-steps:

> **This next step happens in Claude chat (claude.ai), not here.**
>
> Claude chat has a stronger **Research** mode for multi-source web research — that's why we hand off to it once. Follow these steps exactly:
>
> 1. Open **claude.ai** in your browser. Start a new chat.
> 2. Turn on **Research** mode (toggle near the chat input).
> 3. Paste the prompt below. Wait 2–5 minutes while Claude researches.
> 4. Copy the final company list from Claude's response.
> 5. Save it as `target-companies.md` in `<user_dir>/`.
> 6. Come back here to Claude Code and say "continue setup" — I'll pick up from there.
>
> ```
> [the filled-in prompt — include the user's profile verbatim]
> ```

Do NOT attempt to run the deep research yourself in Claude Code. Claude Code's WebSearch is thinner than Claude chat's Research mode — silently substituting it would give the user a weaker target list. The honest path is the handoff.

After printing the block, stop. Wait for the user to come back. Do not continue to Step 9 in the same turn.

## Step 9: Schedule the daily run (batch 4 — 2 questions)

Only reach this after the user has come back with `target-companies.md` (could be later, in a separate invocation).

Ask (batch 4):
1. "Run daily automatically?" (options: Yes at 08:00 local / Yes at a different time / No — I'll run manually)
2. "Which days?" (options: Weekdays only / Every day / Custom)

If yes, try scheduling in this order:

1. **Preferred**: invoke the `/schedule` skill if it's available in the user's Claude Code install.
2. **Fallback**: use the `mcp__scheduled-tasks__create_scheduled_task` MCP tool if present.
3. **Last resort**: if neither is available, write a `<user_dir>/.schedule.yaml` with the requested cron and tell the user: "Scheduling isn't installed on your machine. You'll need to run `/job-search-daily` manually, or install the `schedule` skill from Anthropic. I've saved your preferred time in `.schedule.yaml` so it's ready when you are."

Save the schedule metadata to `<user_dir>/.schedule.yaml` regardless — so `/job-search-status` can report next-run time.

## Step 10: Final summary

```
✅ Job Search OS is set up.

Folder: <user_dir>
CV: <filename> ✅
Profile: ✅ (version 0.1.0)
Target companies: <N> companies across 3 tiers
Sources enabled: <list, e.g. "Finn, LinkedIn, Indeed, Glassdoor">
Schedule: <next run time or "Manual only">

Next steps:
- Type `/job-search-daily` to run the first search now (takes 15–30 min)
- Or wait for <next scheduled run>

Everything is saved in <user_dir>. You can open profile.yaml, sources.yaml, or target-companies.md any time to edit. Changes take effect on the next run.
```

## Don't

- Don't ask questions one at a time. Batch them.
- Don't ask for confirmation before installing dependencies. They're required; user said yes by running setup.
- Don't run deep research yourself. Hand off to Claude.ai.
- Don't block setup if Chrome MCP is missing. Proceed with 3 sources.
- Don't be chatty between steps. One-line status updates only.
