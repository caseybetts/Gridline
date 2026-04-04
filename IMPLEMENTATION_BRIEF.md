# Implementation Brief

### Brief ID
- `FEATURE-RAIL-001`

### Goal
- Sharpen the live in-run command rail so the sidebar reads as an intentional control panel with a clearer crisis-first hierarchy instead of a functional text stack.

### Why This Exists
- The shell and phase-signaling slices are now verified. The next visible product step is to make the live HUD and sidebar feel more authored during active play, especially the pinned status area, section framing, and separation between core run information and lower-frequency controls.

### Source References
- `game_summary.md`: `High-Level UX Direction`, `Presentation Priorities`, `Roadmap Milestones`
- `Game_Design.md`: sections `8`, `8A`, `8B`, and `8C`

### Scope
- In scope:
  - `gridline/app.py`
  - `tests/test_simulation.py`
  - Stronger pinned status hierarchy for corruption, phase, surge, and power state
  - Clearer visual framing for `Run Status`, `Selection`, contextual actions, and utility/menu regions
  - Better separation between high-priority live information and quieter low-frequency controls
  - Sidebar polish that reinforces "board is the hero surface, sidebar is the command rail"
- Out of scope:
  - New simulation mechanics or balance changes
  - Additional shell-state behavior changes
  - New escalation rules
  - Full visual redesign of the board itself

### Ownership / Touch Points
- Primary files:
  - `gridline/app.py`
- Secondary files if needed:
  - `tests/test_simulation.py`
- Do not touch unless required:
  - `gridline/simulation.py`
  - `game_config.json`
  - `gridline/spec.py`

### Implementation Shape
- State/model changes:
  - None expected beyond presentation-facing app state if needed
- UI/rendering changes:
  - Make the top status region read in the approved crisis-first order with clearer visual emphasis on the most urgent rows
  - Add stronger section shells or framing so `Run Status`, `Selection`, contextual actions, and utility areas feel deliberately grouped
  - Keep utility/menu controls visibly quieter than live gameplay controls
  - Preserve stable spacing and button footprints while improving hierarchy, scan order, and readability
  - Keep the board visually dominant; sidebar polish should support it, not compete with it
- Config/spec changes:
  - None for this slice

### Pseudocode / Logic Sketch
```text
1. Keep the current HUD data, but restyle and reorder emphasis so the live crisis reads top-down more clearly.
2. Strengthen the pinned Run Status panel with clearer badges/headers and more deliberate row contrast.
3. Give Selection, action groups, and utility controls more obvious section framing while preserving the stable layout behavior already verified.
4. Reduce the visual weight of low-frequency controls so the main action stack remains the focus.
5. Leave shell flow, phase logic, and simulation behavior untouched.
```

### Constraints
- Do not regress verified shell or phase-signaling behavior.
- Keep the supported-window layout stable and reachable.
- Do not widen this pass into simulation tuning or new interaction design.
- Preserve existing grouped-action stability and overflow behavior.
- The command rail should feel sharper, not busier.

### Acceptance Checks
- Functional checks:
  - The status stack feels easier to scan in the approved priority order during active play
  - Section grouping is more obvious at a glance
  - Utility controls remain reachable but visually secondary
- Regression checks:
  - Existing shell flow still works
  - Existing phase row and banner still work
  - Existing grouped-action stability and supported-window reachability still hold
  - Live gameplay controls still work during `active_run`
- New tests:
  - Add lightweight app-level assertions only where practical; otherwise report concise runtime verification in the handoff back

### Risks / Watchouts
- Easy mistake: making the sidebar louder without making it clearer.
- Easy mistake: breaking the already-stable grouped layout while trying to add more framing.
- Easy mistake: letting visual polish creep into a full sidebar rewrite.
- Do not let low-frequency utility controls pull focus from run-critical status and actions.

### Handoff Back
- Coder should report:
  - What changed in the command-rail hierarchy and section framing
  - How urgency and scan order improved
  - What runtime or test checks were used
- Tester should verify:
  - The command rail reads more clearly during live play
  - Core status still stays pinned and readable
  - Section grouping and utility separation are clearer without regressing reachability
