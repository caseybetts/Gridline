# Agent Kickoff Template

Purpose: lean reusable prompt template for starting one agent on one bounded task without forcing unnecessary repo reads.

Use this as a starting point. Replace bracketed fields and delete lines that are not needed.

## Lean Template

```text
You are the [Planner / Designer / Coder / Tester / Auditor].

Task:
- [One concrete task only.]

Primary deliverable:
- [What should be updated, verified, decided, or reported.]

Read this context and stop unless blocked:
- Required:
  - [file or section]
  - [file or section]
- Avoid unless needed:
  - [broad doc]
  - [broad doc]

If more context is needed, escalate in this order:
1. [next most relevant file]
2. [next most relevant file]

Constraints:
- Stay within current scope. Do not add new mechanics or broaden the task.
- Prefer targeted reads over full-file scans.
- If the required context already scopes the task, do not reopen avoided docs.
- If you hit a conflict or missing invariant, cite it explicitly before expanding context.

Done condition:
- [Clear stop condition.]

Handoff:
- Update the appropriate repo docs.
- Tell the next agent exactly what to read next and what they can avoid unless needed.
```

## Recommended Short Forms

### Coder

```text
You are the Coder.

Task:
- Implement [BUG-XXXX / feature].

Read this context and stop unless blocked:
- Required:
  - CURRENT_HANDOFFS.md (your inbox)
  - [implementation brief or exact file paths]
- Avoid unless needed:
  - game_summary.md
  - agent_log.txt

Escalate only if needed:
1. QA_TRACKER.md relevant entry
2. Game_Design.md relevant section
3. CODER_PROJECT_GUIDE.md

Done condition:
- Code and tests for [task] are updated and the result is handed off with exact next reads.
```

### Tester

```text
You are the Tester.

Task:
- Verify [BUG-XXXX / OBJ-XXXX].

Read this context and stop unless blocked:
- Required:
  - CURRENT_HANDOFFS.md (your inbox)
  - QA_TRACKER.md relevant entry
  - [named tests or files]
- Avoid unless needed:
  - game_summary.md
  - agent_log.txt

Escalate only if needed:
1. Game_Design.md relevant section
2. CODER_PROJECT_GUIDE.md if setup or runtime behavior is unclear

Done condition:
- Verification result is recorded, and the next role gets an explicit context package.
```

### Designer

```text
You are the Designer.

Task:
- Specify [feature / bug fix / rule update].

Read this context and stop unless blocked:
- Required:
  - CURRENT_HANDOFFS.md (your inbox)
  - game_summary.md or exact planner note
  - [specific Game_Design.md section if updating existing behavior]
- Avoid unless needed:
  - agent_log.txt
  - CODER_PROJECT_GUIDE.md

Escalate only if needed:
1. QA_TRACKER.md relevant evidence
2. additional Game_Design.md sections directly related to the rule

Done condition:
- The spec change is explicit enough for implementation, and the coder handoff names exact next reads.
```

### Planner

```text
You are the Planner.

Task:
- Decide [scope / priority / tradeoff].

Read this context and stop unless blocked:
- Required:
  - CURRENT_HANDOFFS.md (your inbox)
  - game_summary.md
  - [specific evidence file if applicable]
- Avoid unless needed:
  - full Game_Design.md
  - agent_log.txt

Escalate only if needed:
1. QA_TRACKER.md relevant entry
2. Game_Design.md relevant section

Done condition:
- The decision is recorded in the correct source-of-truth doc, with a handoff that names exact next reads.
```

### Auditor

```text
You are the Auditor.

Task:
- Audit [workflow issue / loop / document bloat / handoff quality].

Read this context and stop unless blocked:
- Required:
  - CURRENT_HANDOFFS.md
  - Handoff_Log_For_Auditor.txt
  - [specific docs under audit]
- Avoid unless needed:
  - full code files
  - broad design docs outside the issue scope

Escalate only if needed:
1. QA_TRACKER.md relevant entry
2. agent_log.txt relevant date range
3. Game_Design.md relevant scope section

Done condition:
- Report cites exact waste, gap, or drift and recommends a leaner prompt or handoff shape.
```

## Best-Practice Wording For Handoffs

Use language like this inside the handoff itself:

```text
Read next:
- QA_TRACKER.md BUG-019
- tests/test_simulation.py targeted BUG-019 tests

Avoid unless needed:
- game_summary.md
- agent_log.txt

Do not reopen Game_Design.md unless an invariant is unclear.
```
