# Job Search OS — How to Use

A job-search assistant that lives inside Claude Code. You drop your CV, answer a few questions, and every morning it searches LinkedIn, Finn.no, Indeed, and Glassdoor for roles that match you, writes first-draft cover letters, and keeps a tracker in Excel.

You don't need to know how to code.

---

## What you need

Before you start, make sure you have:

1. **A Claude Pro or Max subscription.** The free tier won't work — this needs Claude Code, which is a Pro feature.
2. **Claude Code installed.** It's Anthropic's terminal app for Claude (different from the Claude Desktop chat app). Install docs: https://docs.claude.com/en/docs/claude-code — the fastest path on macOS/Linux is `npm install -g @anthropic-ai/claude-code`, then run `claude` in a terminal.
3. **A Mac, Linux, or Windows machine.** The setup wizard detects your operating system and runs the correct installer automatically — you don't need to do anything different based on your OS.
4. **The Claude-in-Chrome extension** (only if you want LinkedIn to work — and you probably do). It's free. Install it from the Chrome Web Store and log into LinkedIn once in that browser.
5. **About 15 minutes** for the one-time setup.

You do **not** need a GitHub account. You do not need to know Python, terminals, or anything technical.

---

## One-time setup (five steps)

### Step 1 — Install Claude Code

**macOS / Linux**: open the Terminal app. On macOS, press `⌘+Space`, type "Terminal", hit Enter.

**Windows**: open **Windows Terminal** or **PowerShell** (search either in the Start menu — don't use the legacy `cmd.exe`).

In the terminal you opened, run:
```
npm install -g @anthropic-ai/claude-code
```
Then type `claude` to start. Sign in with your Claude account.

If you don't have Node.js / npm installed yet, install it first:
- **macOS**: https://nodejs.org (LTS) or `brew install node`
- **Linux**: your package manager (`apt install nodejs npm` etc.) or https://nodejs.org
- **Windows**: https://nodejs.org → download the **LTS MSI installer**, run it, restart your terminal

### Step 2 — Install the Chrome extension (for LinkedIn)

Open Chrome, go to the Chrome Web Store, search for "Claude in Chrome", and install the extension. Click the extension once to log in to your Claude account, then open LinkedIn in that same Chrome window and log in to LinkedIn once. That's it — Claude Code can now search LinkedIn on your behalf using your logged-in session.

If you skip this step, LinkedIn will be disabled and the plugin will still work with Finn, Indeed, and Glassdoor. But LinkedIn is the most valuable source, so it's worth doing.

### Step 3 — Install the plugin

In the Claude Code terminal you started in Step 1 (or in Claude Desktop's embedded Code mode — press `⌘+J` on Mac or `Ctrl+J` on Windows to open it), type:

```
/plugin marketplace add pradeep-sankaran-07/job-search-os
```

Press Enter. Then:

```
/plugin install job-search-os
```

Press Enter. Claude Code downloads the plugin and confirms it's installed.

### Step 4 — Run the setup wizard (drop your CV + build your profile in one go)

Type:

```
/job-search-setup
```

Or, in plain English, just tell Claude Code: *"Walk me through setting up my job search."*

What the wizard does, as one continuous flow:
- Picks a folder for your job search (default: `~/Documents/job-search/`) and installs the Python libraries it needs
- Asks you to drop your CV into the folder (PDF or Word doc)
- Reads your CV and asks about 8 short questions in two batches — titles, locations, seniority, industries you like, industries to avoid, and a sample of your own writing (for cover-letter voice)
- Gives you 2–4 concrete recommendations for your CV and (if you want) saves a polished version alongside the original
- Saves your profile and creates your tracker

Everything is saved in your job-search folder. Nothing leaves your computer.

### Step 5 — Build your target-companies list (this one happens in Chat mode, not Code mode)

After your profile is saved, the wizard hands you off to **Chat mode** in the Claude desktop app for one step only. Chat has a stronger **Research** mode for multi-source web research.

Do this exactly:

1. In the Claude desktop app, switch to **Chat** mode (the mode selector has Chat / Cowork / Code).
2. Turn on **Research** mode (the toggle near the chat input).
3. Paste the prompt the wizard printed in Claude Code — your profile is already included.
4. Wait 2–5 minutes while Claude researches.
5. Save Claude's response as `Target Companies.pdf` in your job-search folder. (Easiest way: use the browser's Print → Save as PDF, or Chat's Export if it has one.)
6. Switch back to **Code** mode and say *"continue setup"* (or type `/job-search`).

**If you don't see a "Research" toggle in Chat mode**: not every account has it yet. You can still paste the prompt into a regular chat — Claude will do an abbreviated version. The result will be smaller but still useful. You can always re-run it later if Research becomes available on your account.

---

## Your first day

Once setup is done, type `/job-search` any time and Claude Code will figure out what to do next. On day 1, that's usually "let's run your first search" — takes about 20–30 minutes, mostly waiting while Claude searches each source.

When it's done, you'll have:

- `tracker.xlsx` — every new job it found, with a fit rating and a recommendation (Apply Now / Consider / Skip)
- `cover-letters.docx` — a first-draft cover letter for every Strong fit, plus a short LinkedIn outreach message for each one
- A summary in the chat showing what was found and what was skipped

Open `tracker.xlsx` in Excel or Numbers. Read each job, decide. Mark the Status column "Applied" when you apply, "Will not apply" if you skip it. Tomorrow's run will archive those rows and pull in new ones.

---

## What runs where

| Task | Where it happens |
|---|---|
| CV upload, polish | Claude Code |
| Profile questions | Claude Code |
| **Target-companies research** | **Claude.ai (web) — one-time handoff** |
| Daily job search | Claude Code |
| Reviewing matches, writing cover letters | Claude Code |
| Applying (clicking the apply button) | You, in your browser |

---

## What happens every day

When the scheduled run fires (or when you type `/job-search-daily`), this is what Claude does, in order:

1. Opens your tracker. Moves any "Applied" or "Will not apply" rows to an Archive tab.
2. Searches Finn.no (via a headless browser).
3. Searches LinkedIn (via your logged-in Chrome extension — this is why Step 2 matters).
4. Searches Indeed and Glassdoor (via Python libraries — best-effort; they sometimes block, it keeps going).
5. Deduplicates everything across all four sources.
6. For each new job, opens the actual posting URL in a real browser to confirm it's live (this catches the common case where a job was removed but the link still returns a page).
7. Rates each remaining job as Strong, Moderate, or Poor fit against your profile.
8. Writes a first-draft cover letter for every Strong fit.
9. Writes a short LinkedIn outreach message for every Strong fit (to send to a hiring manager before applying — warm intros get 5x the callback rate).
10. Updates `tracker.xlsx` and `cover-letters.docx`.
11. Prints a summary.

Total time: usually 15–30 minutes.

---

## Adding a job you found yourself

Saw a role on a site that isn't in the default list? Two ways:

**If you have the URL:** `/job-search-add <paste URL>` — Claude fetches it, verifies it's live, rates the fit, adds it to the tracker, and writes a cover letter if it's a Strong fit.

**If you only have a screenshot:** drag the screenshot into Claude Code and say "add this job". Claude reads the image, extracts the details, and does the same thing. Set the Source column to "Manual" in the tracker.

---

## Adding a new job board

In v0.1, the plugin supports Finn, LinkedIn, Indeed, and Glassdoor out of the box. If you want another (e.g., Welcome to the Jungle, StepStone):

```
/job-search-add-source welcometothejungle.com
```

For now, if it's not on the default list, the plugin will tell you and suggest adding jobs manually. Auto-detect support for arbitrary boards is on the roadmap for v0.2.

---

## When something breaks

Type `/job-search-status`. It checks your whole setup:

- Is the job-search folder there?
- Is your CV loaded?
- Is your profile complete?
- Is the Chrome extension connected?
- When did the daily run last succeed?
- How many jobs are in the tracker right now?

Whatever's wrong, it tells you what's wrong and offers a one-command fix.

---

## Privacy

- Nothing you type, drop, or generate leaves your computer except:
  - Search queries sent to Finn.no / LinkedIn / Indeed / Glassdoor (the same as if you typed them into those sites yourself)
  - Prompts you send to Claude (Anthropic's standard data handling applies — see their privacy policy)
- Your CV, profile, tracker, and cover letters are stored only in your job-search folder on your Mac/PC.
- The plugin does not phone home, does not send analytics, and has no network calls except the job-site searches above.

---

## A note on the daily schedule

If you said yes to scheduling during setup, Claude Code will run the search automatically at the time you picked. This works only when Claude Desktop is running. If you close Claude Desktop, the schedule pauses and resumes when you next open it.

To cancel or change the schedule, just re-run `/job-search-setup` and pick a new time (or "no schedule").
