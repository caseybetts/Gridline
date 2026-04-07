# Implementation Brief Template

Purpose: temporary execution brief for one concrete coding task.

Use this when a role has already decided what should be built and the Coder needs a compact technical brief that is more specific than a handoff but less broad than the permanent design docs.

Do not use this file as a long-running backlog, status board, or source of truth.

## When To Use
- Use for one bounded task, bug, or feature slice.
- Use when the Coder would otherwise need to infer too much implementation structure from `Game_Design.md`.
- Skip it for trivial edits where `CURRENT_HANDOFFS.md` is already enough.

## What This File Is Not
- Not a replacement for `game_summary.md`
- Not a replacement for `Game_Design.md`
- Not a replacement for `CODER_PROJECT_GUIDE.md`
- Not a QA tracker
- Not a chronology log

## Lifecycle
1. Create a brief only for the active task.
2. Link to it from `CURRENT_HANDOFFS.md` if the Coder needs it.
3. Keep it concise and technical.
4. Delete, replace, or archive it after the task is resolved.

## Template

### Brief ID
- `BUG-XXXX` or `FEATURE-XXXX`

### Goal
- One sentence describing the intended outcome.

### Why This Exists
- One short paragraph explaining why a plain handoff is not enough.

### Source References
- `game_summary.md`: relevant vision constraint(s)
- `Game_Design.md`: relevant behavior/spec sections
- `QA_TRACKER.md`: relevant bug/objective if applicable

### Scope
- In scope:
  - Exact files or modules that may be changed
  - Exact behavior to implement or correct
- Out of scope:
  - Explicit non-goals
  - Systems that must not be expanded

### Ownership / Touch Points
- Primary files:
  - `path/to/file`
- Secondary files if needed:
  - `path/to/file`
- Do not touch unless required:
  - `path/to/file`

### Implementation Shape
- State/model changes:
  - New fields, data flow, or invariants
- Control flow changes:
  - Update order, event order, or function call order
- UI/rendering changes:
  - What must change visually and what must stay stable
- Config/spec changes:
  - Any values or keys that need to move into config/spec

### Pseudocode / Logic Sketch
```text
1. On X, do Y.
2. If A, branch to B.
3. Preserve C invariant before D happens.
4. Emit/update E after F completes.
```

### Constraints
- Rules that must remain true after the change
- Existing behaviors that must not regress
- Performance or readability constraints if relevant

### Acceptance Checks
- Functional checks:
  - What should be true in runtime behavior
- Regression checks:
  - Existing tests that must still pass
- New tests:
  - Specific tests to add or extend

### Risks / Watchouts
- Likely failure modes
- Easy mistakes
- Ambiguities the Coder should not silently resolve

### Handoff Back
- What evidence the Coder should provide after implementation
- What the Tester should verify

## Writing Rules
- Keep it under roughly one to two screens when possible.
- Prefer bullets over long prose.
- Name exact files and invariants.
- Do not restate large chunks of `Game_Design.md`; point to the relevant section instead.
- Do not include project history, sprint narrative, or role chatter.
- If the brief starts looking permanent, move durable parts into the proper source-of-truth doc and shrink the brief again.

## Example Stub

### Brief ID
- `BUG-019`

### Goal
- Make later power funding reach a real charge/deploy decision without reopening the early full-rush exploit.

### Source References
- `game_summary.md`: power tower is an emergency stabilizer, not the dominant default strategy
- `Game_Design.md`: Section 20 tuning rules
- `QA_TRACKER.md`: `BUG-019`

### Scope
- In scope:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`
  - `tests/test_simulation.py`
- Out of scope:
  - new tower types
  - new enemy behaviors
  - UI redesign

### Implementation Shape
- Adjust existing economy/pacing/funding levers only.
- Keep the minute-two floor intact.
- Preserve blocked early full-charge rush behavior.

### Acceptance Checks
- Mixed and power-leaning competent lines can reach a meaningful charge or deploy decision.
- Existing guard regressions still pass.
- New or updated regression coverage reflects the tuned lane.
