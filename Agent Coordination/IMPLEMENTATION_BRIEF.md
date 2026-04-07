# Implementation Brief

### Brief ID
- `FEATURE-RAIL-002`

### Goal
- Implement the finalized GUI/presentation slice for compact harvest attribution, board-edge framing, and ready-shell background treatment without reopening Section `20` balance work.

### Why This Exists
- The current Coder handoff spans several `Game_Design.md` sections and three separate UI decisions. A short brief is better here because the work is bounded but spread across a few specific `gridline/app.py` seams, and the main risk is drifting into unrelated sidebar polish or power retuning.

### Source References
- `game_summary.md`: `High-Level UX Direction`, `Presentation Priorities`
- `Game_Design.md`: sections `7`, `8`, `8A`, `8B`, `8C`, `9`, `17`, and `20`
- `Agent Coordination/CURRENT_HANDOFFS.md`: active Coder inbox for this slice

### Scope
- In scope:
  - `gridline/app.py`
  - `tests/test_simulation.py`
  - Compact ship-facing harvest attribution in the status rail and selection details
  - Board boundary treatment that reads as darker outer margin plus subtle inset outline
  - Ready-shell background treatment that reads as dimmed board preview plus command-surface scrim while keeping `Start Run` obviously primary
- Out of scope:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`
  - Section `20` pacing or power-tower rebalance
  - New shell states, new mechanics, or broader sidebar redesign

### Ownership / Touch Points
- Primary files:
  - `gridline/app.py`
- Secondary files if needed:
  - `tests/test_simulation.py`
- Do not touch unless required:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`

### Implementation Shape
- State/model changes:
  - None expected beyond minor presentation helpers in `GridlineApp`
- Control flow changes:
  - Keep current shell-state and sidebar refresh order intact; this is a presentation pass, not a loop/state rewrite
- UI/rendering changes:
  - In `_refresh_sidebar()` and `_recent_harvest_text()`, keep one concise `Harvest` row in status and keep tower-specific income detail only in selection context
  - In the selected tower detail text, preserve the economy block but avoid turning it into a permanent debug-style telemetry strip
  - In `_render()`, keep the existing `board_surface` rect aligned exactly to `topology.playfield_rect`, but make the off-board canvas read as darker non-playable margin and the board edge read as a subtle inset outline
  - In `_shell_presentation()` and `_render_shell_overlay()`, treat `title_ready` as a board-preview shell: dim/scrim the board, keep the shell panel crisp, and preserve `Start Run` as the dominant action at the support floor
- Config/spec changes:
  - None expected; use existing visual values unless a tiny app-local constant addition is clearly needed

### Pseudocode / Logic Sketch
```text
1. Keep the harvest popup on the board.
2. Shorten the status Harvest row so it reports recent income compactly instead of repeating full tower/mode detail.
3. Leave richer recent-income context only in the selected tower detail block.
4. In board render, darken the full canvas background outside playfield_rect and draw a subtle cool-toned outline on the board_surface rect.
5. In title_ready shell render, let the board remain visible underneath but apply a dim/scrim treatment so the shell panel and Start Run control stay visually primary.
6. Keep pause/defeat behavior and current shell flow unchanged.
```

### Constraints
- Preserve the verified `board_surface` geometry at `topology.playfield_rect`.
- Preserve supported-window reachability at `1280x720`.
- Do not remove local harvest popups.
- Do not remove contextual selected-tower economy detail.
- Do not reopen deeper power-tower usability/value tuning beyond keeping the current UI readable.
- Avoid full-sidebar restyling; the target is this exact spec slice.

### Acceptance Checks
- Functional checks:
  - Status rail shows compact harvest attribution rather than a long debug-style sentence
  - Selected tower details still expose recent-income context when a tower is selected
  - Off-board space reads as background, while the board edge reads as a deliberate bounded frame
  - `title_ready` visibly uses the board as subdued background context and still keeps `Start Run` visually primary
- Regression checks:
  - `tests/test_simulation.py::test_harvest_income_creates_popup_and_selected_tower_economy_snapshot`
  - `tests/test_simulation.py::test_sidebar_uses_contextual_action_groups`
  - `tests/test_simulation.py::test_rendered_board_surface_uses_topology_playfield_rect`
  - `tests/test_simulation.py::test_shell_flow_boot_pause_resume_and_defeat_replay`
- New tests:
  - Extend or add lightweight app-level assertions for the shortened harvest row text
  - Extend shell/board tests only where needed to confirm the ready-shell overlay still exposes the expected primary-action language and the board surface remains correctly framed

### Risks / Watchouts
- Easy mistake: shortening harvest text so far that the player loses the sense of a recent income event.
- Easy mistake: changing board framing by moving the actual `board_surface` coordinates instead of only changing its treatment.
- Easy mistake: making the ready shell too opaque and effectively hiding the board, or too weak and letting the shell panel lose primacy.
- Easy mistake: drifting into a larger command-rail redesign because the older brief in this file was broader.

### Handoff Back
- Coder should report:
  - Which of `_refresh_sidebar()`, `_recent_harvest_text()`, `_render()`, `_shell_presentation()`, and `_render_shell_overlay()` changed
  - What tests or runtime probes were used
  - Confirmation that Section `20` balance surfaces were untouched
- Tester should verify:
  - Harvest attribution now reads compactly in status while remaining contextual in selection details
  - Board-edge framing reads as bounded playfield, not extended grid
  - `Start Run` remains visually primary and reachable in the ready shell at `1280x720`
