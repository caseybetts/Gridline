  - Fewer repeated “planner updated summary, sync design doc” prompts when no newer planner entry
    exists. If you reference the exact entry_id, I can jump straight to the delta.
  - Shorter source docs or clearer layering. game_summary.md, Game_Design.md, QA_TRACKER.md, and
    agent_log.json all overlap, so I often have to re-read multiple files to confirm authority.
  - A stable convention for “active source of truth”. For example:
      - game_summary.md: high-level approved direction
      - Game_Design.md: implementation-ready rules only
      - agent_log.json: handoffs only, not long-running requirements
  - Smaller log tails. agent_log.json is useful, but it’s growing into a history archive. A
    separate current_handoffs.md or “latest per role” section would reduce scanning.
  - Explicit “only use deltas” requests. If you say “apply only planner-20260325-005”, I don’t
    need to re-check adjacent entries as aggressively.
  - More targeted asks. “Update HUD section only” is much cheaper than “carry summary changes into
    design doc” when the change is narrow.
  - Avoid asking me to restate work already completed unless you suspect a missed newer entry.
    That tends to spend context on verification instead of progress.


  Better prompt:
    Read CURRENT_HANDOFFS.md, execute the active task assigned to the next role end-to-end, then update CURRENT_HANDOFFS.md,
  QA_TRACKER.md, and agent_log.txt as needed with the outcome.