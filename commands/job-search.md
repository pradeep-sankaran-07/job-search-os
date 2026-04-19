---
description: Main entry to Job Search OS. Diagnoses your setup state and runs the next needed step automatically.
---

Run the `job-search-diagnose` skill to assess the state of the user's Job Search OS setup. Based on the state, route to the right next action:

- State `no_folder` or `no_profile` or `no_cv` → invoke `job-search-onboarding` skill.
- State `no_targets` → print the deep-research handoff prompt (from `job-search-onboarding` Step 8) and stop; user must complete in Claude.ai.
- State `no_schedule` → ask one question ("Schedule daily runs?") and set it up via `/schedule`.
- State `ready` or `stale` → present three options via a single `AskUserQuestion`:
  1. "Run today's search now" → invoke `job-search-daily`
  2. "Add a job manually" → prompt for URL/paste/screenshot, then invoke `job-search-add-job`
  3. "Just show me status" → print the diagnose report (already done above) and stop.

Do NOT re-ask setup questions if the state is partial. Resume from where the user left off — the onboarding skill detects existing state and picks up mid-flow.

Do NOT pause between diagnose and the next action. Diagnose, print, act.
