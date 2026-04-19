---
description: First-time setup wizard. Creates your job-search folder, installs dependencies, collects your profile, handles CV intake, and schedules daily runs.
---

Invoke the `job-search-onboarding` skill. It handles:

1. Folder creation
2. Settings merge (permission allowlist)
3. Dependency install
4. Chrome MCP detection
5. CV intake
6. Profile Q&A (2 batches, 8 questions)
7. Tracker creation
8. Deep-research handoff to Claude.ai for target companies
9. Daily-schedule setup
10. Final summary

The skill detects existing state — re-running `/job-search-setup` resumes from whatever step is incomplete rather than starting over.

Target: ≤ 4 `AskUserQuestion` batches total, ≤ 3 permission prompts.
