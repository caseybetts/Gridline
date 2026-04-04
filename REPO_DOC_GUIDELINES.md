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
- high-level intent summaries that point to deeper spec sections when exact behavior matters
  Not for:
- code structure
- implementation walkthroughs
- detailed rebuild steps
- active phase, blockers, sprint goals, live risks, or current defers
- stacked historical milestone states such as multiple old `Current batch after...` notes
- exact mechanic mappings, numeric defaults, procedures, or other spec-level detail that already belongs in `Game_Design.md`
- copying large sections of implementation-ready rules out of `Game_Design.md`
  Think of it as: what the game is, and the key rules it must obey.

  Maintenance rules:
- Keep this file state-agnostic. If a sentence depends on "current", "active", "latest", or a sprint phase, it probably belongs somewhere else.
- Move chronology to `agent_log.txt`, live work to `CURRENT_HANDOFFS.md`, and verification status to `QA_TRACKER.md` instead of preserving them here.
- If `game_summary.md` needs exact rule wording, add a short pointer to `Game_Design.md` instead of duplicating the rule text.
- If a mechanic, mapping, constant, or procedure is already specified in `Game_Design.md`, treat that spec as canonical and keep `game_summary.md` at the intent level.

## Game_Design.md

  Purpose: designer-owned implementation-ready game specification.
  Scope:

- system-by-system gameplay rules
- UI/UX behavior requirements
- exact mechanic definitions
- data requirements
- state flows
- approved starter constants and numeric defaults
- durable tuning and playtest rules that should remain true across batches
Not for:
- code architecture history
- agent workflow notes
- long-running project coordination
- active batch status, current blockers, or sprint-specific priorities
- "how to rebuild the repo from scratch" at an engineering level
Think of it as: how the game should behave.

  Maintenance rules:
- Keep this file state-agnostic. Do not store temporary batch evidence, active bug references, or "next pass" instructions here.
- If a rule is only true for the present work cycle, it belongs in `CURRENT_HANDOFFS.md` or `QA_TRACKER.md`, not in this spec.
- Prefer durable acceptance criteria and durable tuning principles over live-status summaries.

## CODER_PROJECT_GUIDE.md

  Purpose: coder-owned reconstruction and implementation guide.
  Scope:

- how the codebase is organized
- what files do what
- how to rebuild the project from scratch
- implementation order
- runtime architecture expectations
- coding guardrails
- durable implementation notes that remain useful after backlog or status changes
Not for:
- changing gameplay direction on its own
- becoming the primary design authority
- replacing game_summary.md or Game_Design.md
- live backlog, active bug queue, sprint status, or recently completed work
Think of it as: how to build the game in code, and how to recover if the
codebase is lost.

  Maintenance rules:
- Keep this file state-agnostic. If content is about what to do now, what just landed, or what is blocked, move it to `CURRENT_HANDOFFS.md`, `QA_TRACKER.md`, or `agent_log.txt`.
- Use this file for rebuild order, architecture, file responsibilities, and coding guardrails that stay useful even if the project is recreated from zero.

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
- keep entries strictly sorted by timestamp from oldest to newest
- if an older/backfilled entry is added later, insert it chronologically instead of appending it to the end

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

## Anti-Rot Rules

- Do not let `game_summary.md`, `Game_Design.md`, or `CODER_PROJECT_GUIDE.md` carry active state or historical timeline. Active state belongs in `CURRENT_HANDOFFS.md` or `QA_TRACKER.md`; history belongs in `agent_log.txt`.
- Do not duplicate exact mechanic rules across `game_summary.md` and `Game_Design.md`. Keep intent in the summary and exact behavior in the spec.
- When a higher-priority source-of-truth doc becomes stale after a verified change, update that doc in the same work batch or hand off that reconciliation explicitly.

## Lean Context Protocol

- Read for the active task, not for completeness theater.
- `REPO_DOC_GUIDELINES.md` and your own `CURRENT_HANDOFFS.md` section are the universal starting point.
- After that, stop and ask: "Is the task already fully scoped by the inbox message or implementation brief?" If yes, work from that scoped context instead of reopening broad docs.
- Treat the read-order lists below as escalation order, not a command to read every file every turn.
- Open broad docs only when you need the specific thing they own:
  - `game_summary.md` for product intent and non-negotiable scope
  - `Game_Design.md` for exact gameplay behavior or UX rules
  - `CODER_PROJECT_GUIDE.md` for engineering structure and rebuild guidance
  - `QA_TRACKER.md` for pass/fail targets and current bug/objective status
  - `agent_log.txt` for chronology, sequence, or "what changed when"
- Prefer targeted section reads, search hits, and cited excerpts over full-file rereads.
- If a handoff or brief explicitly says a broad doc does not need to be reopened for the active task, honor that unless you hit a conflict, missing invariant, or verification gap.
- Use "do not reopen X unless needed for Y" wording rather than absolute bans. The goal is to cut waste without making agents blind.

## Recommended Escalation Order

  These are escalation paths, not startup checklists.
  Start with the first two items, then stop as soon as the task is fully scoped.

  Planner:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. exact evidence file or section named in the inbox
4. `game_summary.md`
5. `agent_log.txt`

  Designer:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. exact planner note or relevant `game_summary.md` section
4. relevant `Game_Design.md` section
5. `QA_TRACKER.md` evidence if needed
6. `agent_log.txt`

  Coder:

1. `repo_doc_guidelines.md`
2. `CURRENT_HANDOFFS.md`
3. implementation brief or exact files/tests named in the inbox
4. relevant `QA_TRACKER.md` entry
5. relevant `Game_Design.md` section
6. `game_summary.md` if product intent is unclear
7. `CODER_PROJECT_GUIDE.md` if engineering structure or rebuild context is unclear
8. `agent_log.txt`

  Tester:

1. `REPO_DOC_GUIDELINES.md`
2. `CURRENT_HANDOFFS.md`
3. relevant `QA_TRACKER.md` entry or named test target
4. relevant `Game_Design.md` section
5. `game_summary.md` if scope intent is unclear
6. `CODER_PROJECT_GUIDE.md` if setup or runtime behavior is unclear
7. `agent_log.txt`

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
  any agent, or `empty` if there is nothing new to handle. Keep the
  field as one message, but prefer a structured message body inside it
  for anything non-trivial.
- `Deferred`: one follow-up item that should wait until after the
  current work or dependency is cleared, or `empty` if there is none.
  Use the same message style as `Current Inbox`, usually in a shorter
  form.
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
- Be explicit about context so the next agent does not have to rediscover it:
  - name the exact file(s), section(s), test(s), or code surface they should read next
  - say which broad docs they do not need to reopen unless blocked
  - if the task is fully scoped in a brief, point to the brief instead of pasting the full technical detail into the handoff
- Good handoffs minimize search. Bad handoffs force the next agent to reread half the repo.

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

  Keep the file schema unchanged. The structure lives inside the text of
  `Current Inbox` or `Deferred`, not as new top-level fields.

  Use one of these two message forms:

#### Short Form

- Use for trivial tasks that do not need extra context.
- Format:
  - `from [Role] - [one concrete action].`

#### Expanded Form

- Use for anything that would otherwise become a dense paragraph.
- Put the structure inside the single `Current Inbox` or `Deferred`
  value.
- Recommended fields:
  - `Task`
  - `Read next`
  - `Avoid unless needed`
  - `Done condition`
- Optional fields:
  - `Evidence`
  - `Blocked by`
  - `Brief`

  Template:

```text
from [Role] -
Task:
- [one concrete action]

Read next:
- [exact file / section / test]
- [exact file / section / test]

Avoid unless needed:
- [broad doc]
- [broad doc]

Done condition:
- [what counts as complete]

Evidence:
- [optional result, failure, or constraint]

Brief:
- [optional brief file]
```

  Example short form:

- `from Planner - Update sidebar priorities in Game_Design.md to reflect the approved usability-first sprint scope.`
- `from Tester - Recheck BUG-010 after the seeder telegraph direction fix lands in gridline/app.py.`

  Example expanded form:

```text
from Tester -
Task:
- Recheck BUG-019 qualitative pass.

Read next:
- QA_TRACKER.md BUG-019
- tests/test_simulation.py targeted BUG-019 tests

Avoid unless needed:
- game_summary.md
- agent_log.txt

Done condition:
- Confirm close vs reopen and update QA_TRACKER.md.

Brief:
- BUG-019 brief
```

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


## IMPLEMENTATION_BRIEF_TEMPLATE.md
  Purpose: temporary execution brief for one bounded coding task when a
  normal handoff is too thin but the durable docs are too broad.

  Use it when:
- the Coder needs exact files, invariants, implementation shape, or test expectations for one active task
- `CURRENT_HANDOFFS.md` can point to a brief instead of carrying a long technical message

  Do not use it for:
- long-running backlog
- project history
- source-of-truth design decisions
- replacing `CURRENT_HANDOFFS.md`, `QA_TRACKER.md`, or the durable docs

  Think of it as:
- `CURRENT_HANDOFFS.md` = coordination
- `IMPLEMENTATION_BRIEF_TEMPLATE.md` = execution detail

  Maintenance rules:
- Keep the brief scoped to one active task, bug, or feature slice.
- Keep it concise and technical.
- Remove, replace, or archive the brief after the task is resolved.
- If content in the brief becomes durable project knowledge, move that part into the proper source-of-truth doc and shrink the brief again.
- Include a short "Read next / Avoid unless needed" note when the brief is meant to replace broad rediscovery.


## Handoff_Log_For_Auditor.txt
- Use one plain-text line per entry in this exact order:
  `[Timestamp][Sending Agent][Receiving Agent][Handoff Text]`
- Handoff Text should be exactly what was added to the Current Inbox or Deffered field
- If multiple handoffs were made, add each one as a separate line
