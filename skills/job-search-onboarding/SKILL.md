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

## Step 3: Install dependencies silently

Run in one shot:

```bash
bash <plugin_dir>/scripts/install_deps.sh
```

This installs Python deps (`python-jobspy openpyxl python-docx pandas pyyaml`) and registers the Playwright MCP server if not already present. If any step fails, surface the error but do NOT abort — the user can retry later and some pieces (manual add, profile collection) still work without all deps.

Do not ask the user "should I install?" — if they ran `/job-search-setup`, consent is implicit.

## Step 4: Detect Chrome MCP (for LinkedIn)

Check whether `mcp__Claude_in_Chrome__navigate` is available (list MCP tools).

If yes: set `sources.yaml -> linkedin.enabled: true`, note to the user that LinkedIn is ready.

If no: keep LinkedIn disabled. Tell the user:
> "LinkedIn needs the Claude-in-Chrome extension. Install it from the Chrome Web Store (search 'Claude in Chrome'), sign in with your Claude account, and log into LinkedIn in that Chrome window. Then re-run `/job-search-setup` and I'll enable it."

Do NOT block the rest of setup on this. Proceed.

## Step 5: CV intake

Check `<user_dir>/cv/` for any file. If empty:
- Tell the user: "Drop your CV (PDF or .docx) into `<user_dir>/cv/`, or drag it into this chat." Wait for the file to appear.
- Read the CV (PDFs via `python-docx` for .docx or a PDF library; fall back to OCR if needed).
- Extract: name, email, phone, current/last title, location, years of experience.
- Offer ONE thing: "Want me to sharpen this CV for punch and modern formatting? (yes / no)". This is not a batch — it's a yes/no. Add it to batch 2 instead.

If a CV is already there: read it, note "Found `<filename>`".

## Step 6: Profile Q&A (batches 2 and 3)

Collect the profile via 2 batches of `AskUserQuestion`.

**Batch 2 — the basics** (4 questions):
1. "What job titles are you targeting?" (free-text multi-select or "Other" for custom)
2. "What seniority level?" (IC / Manager / Director / VP / C-level)
3. "Where will you work?" (multi-select: Norway / Nordic / Remote Europe / Remote Global / Specific city)
4. "Should I sharpen your CV for you?" (Yes — overwrite existing / Yes — save as new file / No — leave it)

**Batch 3 — preferences and filters** (4 questions):
1. "What industries / domains are you interested in?" (multi-select: B2B SaaS / AI / Fintech / Marketplace / Industrial / Healthcare / Other)
2. "What company stages are okay?" (multi-select: Seed / Series A / Series B / Series C+ / Public / Any)
3. "Any dealbreakers? What should I NEVER show you?" (multi-select: Crypto/Web3 / Hardware / Consumer goods / Staffing/Contract / Pre-sales / None)
4. "Paste 1-2 sentences of your own writing (email to a peer, a LinkedIn post, anything) — I'll use it to match your voice in cover letters. Optional — you can skip." (Other for free-text paste; empty = skip)

Write the answers to `<user_dir>/profile.yaml`, filling in the template from `<plugin_dir>/templates/profile.yaml`. Also fill in name/email/phone/linkedin from the CV you read in Step 5.

## Step 7: Create tracker

Run:
```bash
python3 <plugin_dir>/templates/tracker_schema.py <user_dir>/tracker.xlsx
```

Also create an empty `<user_dir>/cover-letters.docx` (one paragraph placeholder) so later skills can append cleanly.

## Step 8: Target-companies handoff (one-time, happens on Claude.ai)

Generate the deep-research prompt by reading `<plugin_dir>/templates/deep_research_prompt.md` and filling in the `{{...}}` placeholders from `profile.yaml`.

Print it in a fenced block with clear instructions:

> **One-time handoff — do this on Claude.ai, not here.**
>
> 1. Open https://claude.ai in your browser.
> 2. Start a new chat. Click the "Research" toggle at the bottom.
> 3. Paste this prompt (copy it from the block below).
> 4. Wait 2–5 minutes for research.
> 5. Copy the final list.
> 6. Save it as `<user_dir>/target-companies.md`.
> 7. Come back here and type `/job-search` — I'll pick up from there.
>
> ```
> [the filled-in prompt]
> ```

Do NOT try to run the deep research yourself in Claude Code — the whole point is that Claude.ai's Research mode is stronger for this. Don't substitute a WebSearch call.

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
