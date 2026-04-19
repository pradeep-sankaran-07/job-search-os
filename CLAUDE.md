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

## 11. Self-correct across platforms (macOS / Linux / Windows)

The user is non-technical. If a command fails because the expected binary isn't present, fall through these fallbacks **silently** — do NOT prompt the user to fix it themselves.

### OS detection (do this once at the start of any new shell-using flow)

```bash
# macOS/Linux/Windows detection — prefer Python since it's cross-platform
python3 -c "import platform; print(platform.system())"
# Prints: "Darwin" (macOS), "Linux", or "Windows"
```

If `python3` isn't on PATH, try `python` then `py`. If none work, fall back to shell-only detection: `$OS` env var (`"Windows_NT"` on Windows) and `uname -s` (Darwin/Linux).

### Python binary

Windows installers ship `python.exe` or `py.exe` — NOT `python3`. When invoking Python in any skill step, try these in order and use the first that works:

1. `python3` (macOS / Linux / Windows-Store Python shim)
2. `python` (typical Windows python.org installer)
3. `py -3` (Windows `py` launcher)

If the onboarding wizard wrote `<user_dir>/.python-bin`, read that file and use the binary name it contains. The install scripts write this file after they successfully detect Python.

**Special case for the Windows `py` launcher**: if `.python-bin` contains just `py`, always invoke it as `py -3 ...` (not bare `py`) to force Python 3. On machines that still have Python 2 registered, bare `py` can dispatch to Python 2 and imports like `python-jobspy` will fail.

### Install scripts

| Platform | Command |
|---|---|
| macOS / Linux | `bash <plugin_dir>/scripts/install_deps.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File <plugin_dir>\scripts\install_deps.ps1` |

Detect the OS first (see above). Do not ask the user which one to run.

### Shell command portability

- **`grep`**: not reliably on Windows. If you need to filter output, pipe through Python instead: `claude mcp list | python3 -c "import sys; print('ok' if 'playwright' in sys.stdin.read() else 'missing')"`.
- **`ls`**: works in PowerShell as an alias but flags like `-la` don't; prefer `python3 -c "import os; print(os.listdir('.'))"`.
- **`mkdir -p`**: use `python3 -c "from pathlib import Path; Path('...').mkdir(parents=True, exist_ok=True)"`.
- **`cat`**, **`which`**: cross-platform via Python — `Path(...).read_text()`, `shutil.which(...)`.

When in doubt, prefer a short Python one-liner over a shell command. Python behaves the same everywhere.

### Node / npm / npx / claude

On Windows, these are `.cmd` shims. If calling them by bare name fails (because `PATHEXT` resolution didn't fire), try appending `.cmd` (e.g. `npm.cmd`), or resolve via `(Get-Command npm -ErrorAction SilentlyContinue).Source` in PowerShell.

Global `npm install -g` on Windows often needs admin (writes under `Program Files`). If the user's `npm config get prefix` points under `Program Files`, advise them to either re-run as admin or set `npm config set prefix "$env:APPDATA\npm"` and try again.

### Paths

- Always use `pathlib.Path.home() / "Documents" / "job-search"` or `os.path.expanduser("~/Documents/job-search")`.
- Never hardcode `/Users/...`, `/home/...`, or `C:\Users\...`.
- `expanduser` returns platform-appropriate paths automatically.

### OneDrive redirect (Windows)

On many Windows 10/11 machines with a Microsoft account, `~/Documents` is redirected to `C:\Users\<user>\OneDrive\Documents`. This syncs your tracker/CV/letters to the cloud — which may be fine, but can cause file-lock conflicts when Excel has the tracker open during a scheduled run.

During onboarding, detect this: if `os.path.expanduser("~/Documents")` resolves to a path containing "OneDrive", warn the user and offer `~/job-search` (outside Documents) as an alternative default.

### Scheduling fallback

The preferred order for setting up the daily run:
1. `/schedule` skill (Anthropic's scheduler, if installed)
2. `mcp__scheduled-tasks__create_scheduled_task` MCP tool (if connected)
3. Platform-native fallback with explicit instructions for the user. The trigger in every case is `claude -p "/job-search-daily"` (the `-p` / `--print` flag runs a slash command headlessly):
   - **macOS**: write a `launchd` plist that runs `claude -p "/job-search-daily"` on the chosen cron, tell the user to drop it into `~/Library/LaunchAgents/`
   - **Linux**: print a `crontab -e` line: `0 8 * * 1-5  claude -p "/job-search-daily"`
   - **Windows**: print `schtasks /Create /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:00 /TN "Claude Job Search" /TR "cmd /c claude -p \"/job-search-daily\""`
4. Last resort: tell the user "scheduling isn't installed on this machine; you'll need to run `/job-search-daily` each morning yourself" and set `schedule: manual` in `<user_dir>/.schedule.yaml`.

Do NOT just write a cron-syntax yaml and promise the user it'll run — that promise fails silently on Windows.

### One governing principle

If a tool invocation fails and you know a platform-appropriate alternative, try it. If you don't know, tell the user what specifically failed (the command + the error message + the platform) rather than surfacing a generic "something went wrong." The diagnose skill exists for this — invoke it when uncertain.

## 12. Self-correct on INTENT, not just on tool failures

Every step in every skill has a specific intent. When a step fails or its expected tool isn't available, read the intent and find another way to hit the same goal. Do not abandon the step.

### The intent of each major step

**Onboarding** (`job-search-onboarding`):
- *Detect state* → so re-running setup resumes instead of starting over. Fallback: `os.path.exists()` on each expected file; skip what's done.
- *Merge permission allowlist* → so later skills run without prompting. Fallback: if writing to `~/.claude/settings.json` fails, continue and accept more prompts at runtime.
- *Install dependencies* → so Python adapters + Playwright MCP are runnable. Fallback: if `pip install` fails, try `--user`, then `--break-system-packages`, then a venv, then tell the user the specific error; the manual-add and profile flows still work without deps.
- *CV intake + profile Q&A* → so Claude knows the user's targeting, seniority, and voice. Fallback: if CV parsing fails, ask the user to paste the CV text; if a Q&A field is ambiguous, assume the most permissive default.
- *Target-companies handoff* → so the user gets a stronger research result from Claude Chat than from Claude Code's WebSearch. Fallback: if the user can't or won't switch to Chat, offer to run a lighter version here with WebSearch and flag it as abbreviated.
- *Schedule* → so the daily run fires without the user thinking about it. Fallback order: `/schedule` skill → scheduled-tasks MCP → platform-native (`launchd` / `cron` / `schtasks`) → manual with a clear reminder.

**Daily search** (`job-search-daily`):
- *Load profile + tracker* → current state of what's already tracked. Fallback: if tracker is corrupt, create a fresh one from `templates/tracker_schema.py` and note the data loss in the summary.
- *Multi-source search* → coverage across every enabled board. Fallback per source: Finn/career-pages via Playwright MCP → if MCP unavailable, skip with a summary note. LinkedIn via Chrome MCP → if extension missing, skip with a note. Indeed/Glassdoor via JobSpy → if blocked, log and continue. **Never crash the whole run because one source failed.**
- *Dedupe + hard-filter* → quality over quantity. Fallback: if a filter rule is ambiguous, surface as "needs manual review" rather than dropping silently.
- *Live-URL verification* → never add a ghost listing. Fallback: if `verify_url.js` can't run (playwright-core not installed), log and skip that candidate. Never write a row marked "live" without actual verification.
- *Assess fit* → signal Strong / Moderate to the user. Fallback: if the fit is ambiguous, mark Moderate and flag for user judgment.
- *Draft cover letters* → remove the friction of writing 30 letters from scratch. Fallback: if the voice snippet is empty, use a neutral professional tone and flag that a voice snippet would help.
- *Write rows* → tracker is the trust surface. Fallback: if Excel file is locked (user has it open), write to a temp file and print "please close Excel and I'll merge."

**Add job** (`job-search-add-job`):
- *Extract details* → enough to filter and rate. Fallback: if vision/WebFetch fails, ask the user for the missing fields (just the missing ones).
- *Verify live* → same trust contract as daily. If no URL, mark ⚠️ Unverified and still write the row.
- *Write row* → consistent with daily schema.

**Diagnose** (`job-search-diagnose`):
- *Report state* → show the user what's set up, what's missing, what to do. Never fix things silently during diagnose; surface, suggest, let the user run the fix.

**Add source** (`job-search-add-source`):
- *Enable/disable* → edit `sources.yaml`. For unknown sources, point the user at the manual-add path.

### Example: self-correction in practice

*Scenario*: User runs `/job-search-daily` on Windows. `python3` isn't on PATH, so the first `python3 templates/...` invocation errors.

**Wrong response**: Surface "python3: command not found" and stop.

**Right response**:
1. Recognize the failure mode (Python binary not resolvable as `python3`).
2. Read `<user_dir>/.python-bin` (written by `install_deps.ps1`) and retry with that binary.
3. If that file doesn't exist either, probe: try `python`, then `py -3`. Use the first that works.
4. Write the resolved binary to `.python-bin` for next time.
5. Continue the skill as if nothing happened. Note the recovery in the summary if it matters.

### When to actually stop

Stop and ask the user only when:
- A **user decision** is genuinely needed (which role to apply to, which CV polish to accept, what their job titles are)
- Data is **missing and can't be inferred** (no CV dropped, no profile set up, no target companies)
- A **trust-surface violation** would occur (writing unverified rows to the tracker, submitting applications)

Do not stop for:
- A tool that's spelled slightly differently on this platform
- A dependency that isn't installed but can be installed silently
- A source that's blocked today but was working yesterday
- A file format that's almost-right (e.g., `.pdf` vs `.md` for target-companies — just read both)
