---
name: session-summary
description: "LLM-powered session summary on /new or /reset, writes to last-session.md"
metadata:
  openclaw:
    emoji: "\U0001F4DD"
    events:
      - "command:new"
      - "command:reset"
    requires:
      config:
        - "workspace.dir"
---

# Session Summary

When `/new` or `/reset` is triggered:

1. Extract recent conversation messages from the session transcript
2. Call LLM (qwen3-coder-plus via bailian) to generate a concise summary
3. Overwrite `<workspace>/memory/last-session.md` with the summary

The summary includes key decisions, pending TODOs, and important context.
Only one file is maintained — each new session overwrites the previous summary.

On new session start, the agent reads `last-session.md` and asks the user
whether to continue where they left off.
