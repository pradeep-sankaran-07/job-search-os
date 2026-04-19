# Job Search OS — How to Use

A job-search assistant that lives inside Claude Code. You drop your CV, answer a few questions, and every morning it searches LinkedIn, Finn.no, Indeed, and Glassdoor for roles that match you, writes first-draft cover letters, and keeps a tracker in Excel.

You don't need to know how to code.

---

## What you need

Before you start, make sure you have:

1. **A Claude Pro or Max subscription.** The free tier won't work — this needs Claude Code, which is a Pro feature.
2. **Claude Desktop installed**. Download: https://claude.ai/download
3. **A Mac or Linux machine.** v0.1 targets macOS and Linux. Windows users: the plugin's dependency installer uses bash; you can run it from WSL (Windows Subsystem for Linux) or Git Bash, but it hasn't been tested on native Windows yet.
4. **The Claude-in-Chrome extension** (only if you want LinkedIn to work — and you probably do). It's free. Install it from the Chrome Web Store and log into LinkedIn once in that browser.
5. **About 15 minutes** for the one-time setup.

You do **not** need a GitHub account. You do not need to know Python, terminals, or anything technical.

---

## One-time setup (six steps)

### Step 1 — Install Claude Desktop

Download from https://claude.ai/download and sign in with your Claude account.

### Step 2 — Install the Chrome extension (for LinkedIn)

Open Chrome, go to the Chrome Web Store, search for "Claude in Chrome", and install the extension. Click the extension once to log in to your Claude account, then open LinkedIn in that same Chrome window and log in to LinkedIn once. That's it — Claude Code can now search LinkedIn on your behalf using your logged-in session.

If you skip this step, LinkedIn will be disabled and the plugin will still work with Finn, Indeed, and Glassdoor. But LinkedIn is the most valuable source, so it's worth doing.

### Step 3 — Install the plugin

Open Claude Desktop. Open Claude Code (press `⌘+J` on Mac or `Ctrl+J` on Windows). In the input, type:

```
/plugin marketplace add pradeep-sankaran-07/job-search-os
```

Press Enter. Then:

```
/plugin install job-search-os
```

Press Enter. Claude Code downloads the plugin and confirms it's installed.

### Step 4 — Run the setup wizard

Type:

```
/job-search-setup
```

The wizard will:
- Pick a folder for your job search (default: `~/Documents/job-search/`)
- Install the Python libraries it needs (one permission prompt, one command)
- Ask you to drop your CV into the folder (PDF or Word doc, your choice)
- Ask about 10 short questions about what you're looking for (title, location, seniority, industries you care about, industries you want to avoid)
- Help you build a target-companies list (more on this in Step 6 below)
- Offer to schedule a daily run at 08:00 (you can say no or pick another time)

Everything is saved in your job-search folder. Nothing leaves your computer.

### Step 5 — Drop your CV

When the wizard asks, drag your CV file into the Claude Code window, or just save it to `~/Documents/job-search/cv/cv.pdf`. Claude will read it and offer to polish it — you can accept or skip.

### Step 6 — Build your target-companies list (this one happens in Claude.ai, not Claude Code)

The wizard will give you a prompt — copy it, open https://claude.ai in your browser, paste it into a new chat, and turn on "Research" (the toggle at the bottom of the input). Claude.ai will spend a few minutes researching companies that match your profile and give you back a list. Copy that list into a file called `target-companies.md` in your job-search folder. Back in Claude Code, type `/job-search` and it will pick up from there.

Why Claude.ai and not Claude Code? Claude.ai has a stronger Research mode for this kind of multi-source web research. Claude Code handles everything else — this is the one handoff.

**If you don't see a "Research" toggle in Claude.ai**: not every account has it yet. You can still paste the prompt into a regular chat — Claude will do an abbreviated version. The result will be smaller but still useful. You can always re-run it later if Research becomes available on your account.

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
