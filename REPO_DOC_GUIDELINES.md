# Repo Docs Use Guide

How to use and how not to use the tracking/communication documents in this repo

## game_summary.md

  Purpose: planner source of truth for product direction.
  Scope:

- core fantasy
- core loop
- major systems
- non-negotiable decisions
- approved high-level UX direction
- planner-approved changes
Not for:
- code structure
- implementation walkthroughs
- detailed rebuild steps
Think of it as: what the game is, and the key rules it must obey.

## Game_Design.md

  Purpose: designer-owned implementation-ready game specification.
  Scope:

- system-by-system gameplay rules
- UI/UX behavior requirements
- exact mechanic definitions
- data requirements
- state flows
- approved starter constants and numeric defaults
Not for:
- code architecture history
- agent workflow notes
- long-running project coordination
- "how to rebuild the repo from scratch" at an engineering level
Think of it as: how the game should behave.

## CODER_PROJECT_GUIDE.md

  Purpose: coder-owned reconstruction and implementation guide.
  Scope:

- how the current codebase is organized
- what files do what
- how to rebuild the project from scratch
- implementation order
- runtime architecture expectations
- current status of systems from an engineering perspective
- open engineering work queue
- coding guardrails
Not for:
- changing gameplay direction on its own
- becoming the primary design authority
- replacing game_summary.md or Game_Design.md
Think of it as: how to build the game in code, and how to recover if the
codebase is lost.

## agent_log.txt

  Purpose: lightweight project chronology.
  Scope:
- one short entry per meaningful work batch
- enough information to reconstruct change order over time
- quick pointers to related `OBJ-*`, `BUG-*`, or other references when applicable
  Not for:
- full narrative handoffs
- long explanations of reasoning
- file-by-file changelogs
- replacing source-of-truth docs
  Think of it as: concise timeline.

  Entry format:
- use one plain-text line per entry in this exact order:
  `[Timestamp][Agent][Change Made][Refs]`
- keep `Change Made` to one short sentence
- keep `Refs` compact, for example `[BUG-014, OBJ-013]` or `[]` if none apply
- do not use JSON objects for entries

  A simple filter is:
- Log it if another future agent would benefit from seeing that this work happened in sequence.
- Do not log it if it only says "processed inbox" or repeats unchanged status.

  Example:
- `[2026-03-28T10:30:00-06:00][Coder][Exposed power funding chunk cost to config and tuned live economy values for BUG-014 retest.][BUG-014, OBJ-013, OBJ-014]`
- The bracketed line format above is the active rule and supersedes older agent-log wording.
- Do not log it if it only says “processed inbox, updated handoff,
  waiting for next role.”

## QA_TRACKER.md

  Purpose: tester/reviewer validation queue.
  Scope:

- open bugs
- objectives
- verification status
- pass/fail criteria
Not for:
- primary design
- primary implementation guidance
Think of it as: what still needs to be proven.

### In short:

- game_summary.md = planner truth
- Game_Design.md = gameplay spec
- CODER_PROJECT_GUIDE.md = engineering/rebuild guide
- CURRENT_HANDOFFS.md = latest actionable work
- agent_log.txt = chronology of meaningful changes
- QA_TRACKER.md = validation

### The clearest one-line definitions would be:

- game_summary.md: "What game are we making?"
- Game_Design.md: "How should it behave?"
- CODER_PROJECT_GUIDE.md: "How do we build or rebuild it?"
- CURRENT_HANDOFFS.md: "What should each role do right now?"
- agent_log.txt: "What changed, and when?"
- QA_TRACKER.md: "What still needs verification?"

## Conflict Resolution

  When documents conflict, use this precedence order:

1. `game_summary.md`
2. `Game_Design.md`
3. `CURRENT_HANDOFFS.md`
4. `CODER_PROJECT_GUIDE.md`
5. `QA_TRACKER.md`
6. `agent_log.txt`

  Lower number wins.
  If a lower-priority document conflicts with a higher-priority one,
  update the lower-priority document.

## Recommended Read Order

  Planner:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. `game_summary.md`
4. `agent_log.txt`

  Designer:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. `game_summary.md`
4. `Game_Design.md`
5. `agent_log.txt`

  Coder:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. `CODER_PROJECT_GUIDE.md`
4. `game_summary.md`
5. `Game_Design.md`
6. `QA_TRACKER.md`
7. `agent_log.txt`

  Tester:

1. `REPO_DOC_GUIDELINES.md`
2. `CURRENT_HANDOFFS.md`
3. `game_summary.md`
4. `Game_Design.md`
5. `QA_TRACKER.md`
6. `agent_log.txt`

## Archive And Trim Rules

  Use these rules to keep coordination files small and easy to scan:
- Keep `agent_log.txt` as the active recent-history log, not the
  permanent full archive.
- Archive and trim it whenever it becomes long enough that agents must
  scan excessive history to find current work.
- When trimming, move or copy the full current file into `archive/`
  using a timestamped filename.
- After trimming, create a fresh `agent_log.txt` that keeps:
  - either no lines at all or only a few most recent lines if continuity requires them
- Prefer keeping this file very short. The archive carries the long
  history.

## CURRENT_HANDOFFS.md

  Purpose: keep only the latest actionable state for each role so agents
  can take action without scanning history.

### Core Rules

- This file is a state board, not a message log.
- Keep it short and action-oriented.
- Replace old content instead of stacking notes.
- `Current Inbox` may be empty. Empty means there is no new handoff for
  that role.
- `Deferred` is optional and should contain at most one item.
- Durable decisions belong in `game_summary.md`, `Game_Design.md`,
  `CODER_PROJECT_GUIDE.md`, or `QA_TRACKER.md`.
- Historical record belongs in `agent_log.txt`.
- Agents do not need to check `Deferred` while `Current Inbox` contains
  a clear active instruction.
- Agents should check `Deferred` when `Current Inbox` is `empty` or when
  the current active task has been completed.

### Field Key

- `Current Inbox`: the latest unprocessed instruction for this role from
  any agent, or `empty` if there is nothing new to handle.
- `Deferred`: one follow-up item that should wait until after the
  current work or dependency is cleared, or `empty` if there is none.
- `Next Action`: the single most important thing this role should do
  now.
- `Waiting On`: the person, change, approval, or condition currently
  blocking progress, or `none` if the role is not blocked.

### Ownership Rules

- Any agent may write to another role's `Current Inbox`.
- Any agent may write to another role's `Deferred` only if `Current   Inbox` is already occupied and the new note should wait.
- The role that owns the section is responsible for:
  - reading its own `Current Inbox`
  - deciding its own `Next Action`
  - updating its own `Waiting On`
  - clearing or updating its own `Deferred`
  - clearing `Current Inbox` after the message has been processed
- Other agents should not directly edit another role's `Next Action` or
  `Waiting On` except to fix an obvious formatting mistake.

### Sender Flow

  When Agent A needs to hand something to Agent B:

- Write that handoff into Agent B's Current Inbox field (updating only the User / Project Owner section is NOT sufficient).
- Read Agent B's section first before updating:
  a. If Agent B's `Current Inbox` is `empty`, write the new message there.
  b. If Agent B's `Current Inbox` already has a message:
    - If the new message supersedes the old one, replace `Current Inbox`.
    - If the new message is lower priority and `Deferred` is `empty`,
    write it in `Deferred`.
    - If `Deferred` is already occupied, do not stack more notes.
    Consolidate to one concise deferred item or move durable detail into the
    proper source-of-truth doc and leave only a short pointer here.
- Keep the handoff concise and action-oriented.

### Receiver Flow

  When an agent starts work on its own section:

  1. Read `Current Inbox`.
  2. If `Current Inbox` is not `empty`, interpret the instruction and
  decide what to do.
  3. If `Current Inbox` is `empty`, check whether `Deferred` should now
  become the active task.
  4. Update `Next Action` to the single task you will do now, or set it to
  `none` if nothing is active.
  5. Update `Waiting On` if blocked; otherwise set it to `none`.
  6. If the inbox message has been understood and incorporated into active
  work, clear `Current Inbox`.
  7. If `Deferred` becomes the most important active item, move it into
  `Next Action` and clear `Deferred`.
  8. When the active task changes, replace `Next Action`.
  9. When the active task is fully complete and nothing else is pending,
  set `Next Action` to `none`.

### Completion Rules

- Do not leave processed messages sitting in `Current Inbox`.
- Do not keep stale tasks in `Next Action`.
- If `Deferred` becomes the most important active item, move it into
  `Next Action` and clear `Deferred`.
- If a note becomes a lasting project decision, move it into the proper
  source-of-truth doc and remove it from this file.

### Message Style

  Use short messages in this format:

- `from Planner - Update sidebar priorities in Game_Design.md to reflect   the approved usability-first sprint scope.`
- `from Tester - Recheck BUG-010 after the seeder telegraph direction   fix lands in gridline/app.py.`

### User/Project Owner Section
  Field meaning:
  - Suggested Next Agent: the role you should likely run next.
  - Suggested Next Action: the first thing that next agent should do.
  - Latest Agent: the last agent role that worked meaningfully on the
    project.
  - Last Outcome: one-line summary of what changed, was decided, or was
    verified.

  Ownership rule:
  - The agent finishing its turn should update this section before
    stopping.
  - This section is advisory for the user. It does not override the role
    mailboxes or source-of-truth docs.

### How To Interpret `CURRENT_HANDOFFS.md` In Conflicts

  `CURRENT_HANDOFFS.md` controls coordination priority, not durable
  content authority.

  That means:
  - Use `CURRENT_HANDOFFS.md` to decide what role should do next right
  now.
  - Do not use `CURRENT_HANDOFFS.md` to permanently override gameplay,
  product, engineering, or QA source-of-truth content.
  - If a handoff note conflicts with a durable working document, treat the
  handoff as a prompt to update, verify, or reconcile that document.
  - Once the durable document is updated, remove the temporary handoff
  note.

  In short:
  - `CURRENT_HANDOFFS.md` wins for sequencing.
  - Source-of-truth docs win for lasting content.
