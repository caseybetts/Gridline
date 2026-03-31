# Gridline Coder Project Guide

## Purpose
Use this file as the coder-facing bootstrap and tracking document.
It is meant to do two jobs:

1. Give a future coding agent enough context to start work without rediscovering the project.
2. Break the remaining work into manageable slices with clear status and next actions.

Last updated: `2026-03-25`

## Source Of Truth Order
Read these in this order before changing code:

1. `Coder_Prompt.md`
2. `agent_log.txt`
3. `game_summary.md`
4. `Game_Design.md`
5. `QA_TRACKER.md`

Rules:
- `agent_log.txt` is the compact chronology of recent changes and the first place to check for what landed most recently.
- `game_summary.md` remains the current source of truth unless the Planner explicitly promotes newer design decisions into `Game_Design.md`.
- `Game_Design.md` is the detailed coder spec and numeric baseline.
- `QA_TRACKER.md` is the live validation queue, not the design source.

## Project Objective
Build a playable endless-survival, line-based tower defense where the player contains corruption on a three-tier glowing grid by building edge hardpoint towers, managing upgrades, and using readable, path-faithful orb behavior.

The current MVP must preserve these non-negotiables:
- Gameplay happens on grid lines and intersections, not inside cells.
- The three base towers are `Basic Tower`, `Seed Tower`, and `Burst Tower`.
- Each tower keeps a strong archetype identity and may buy exactly one mapped secondary mode.
- Corruption is the primary fail state. The run ends when corruption exceeds the configured percentage.
- Orbs, enemy telegraphs, and line-state changes must be readable in motion.
- Orbs leave fading trails. Must give a sleak futuristic vibe. 

## Runtime File Map
Use these files as the main coding surface:

| File | Responsibility |
| --- | --- |
| `main.py` | Thin app entry point |
| `gridline/app.py` | Tk app shell, renderer, HUD/sidebar, selection UI |
| `gridline/simulation.py` | Core game state, towers, enemies, line-state logic, actions |
| `gridline/spec.py` | Spec/config loading and approved runtime defaults |
| `gridline/topology.py` | Grid generation, hardpoints, playfield layout |
| `tests/test_simulation.py` | Regression coverage for high-risk gameplay behaviors |
| `game_config.json` | Runtime tuning overrides |
| `game_config_schema.json` | Config validation schema |

## Current Snapshot
This is the highest-signal view of where the MVP stands right now.

| Area | Status | Notes |
| --- | --- | --- |
| App boot and core playable loop | `Active` | A playable build exists and the regression suite is running. |
| Grid topology and hardpoint layout | `Active` | 12 perimeter hardpoints and viewport-aware layout have been implemented. |
| Direct build flow on empty hardpoints | `Active` | Activation gating was removed from the approved flow and runtime. |
| Config/spec alignment with MVP defaults | `Active` | Runtime config was rebased to approved design values. |
| Sidebar structure and readability cues | `Active` | Persistent status, selected-object panel, contextual actions, and utility separation are in place. |
| Base towers and upgrade surface | `Partial` | Core tower systems exist, but remaining live-play verification is still open. |
| Seed Tower flight and landing behavior | `Verify` | `OBJ-005` remains in `verify_fix`. |
| Power tower funding and override restore flow | `Verify` | `OBJ-006` remains in `verify_fix` even though related bugs were closed. |
| Red/green spread arbitration | `Verify` | `OBJ-007` and `BUG-004` still need final validation. |
| Focus Mode tie behavior and dense-combat orb readability | `Verify` | `OBJ-008`, `BUG-007`, and `BUG-008` remain open for live validation. |

## Completed Work
These slices are substantially in place and should not be rebuilt unless a defect or design change requires it:

- Three-tier grid topology and perimeter hardpoint layout.
- Direct build-on-empty-hardpoint flow with no activation step.
- Config-driven runtime values and schema-backed spec loading.
- Distinct neutral grid tier readability improvements.
- Viewport-fit topology handling so perimeter hardpoints stay visible.
- Structured sidebar with persistent status, selected-object details, contextual actions, and separate utility controls.
- Enemy corruption telegraph direction, pulse-on-seed feedback, line-intensity readability ramps, and visible orb-impact feedback.
- Expanded regression coverage up to the current 17-test suite.

## Open Work Queue
Treat these as the current coder-facing backlog. Work from top to bottom unless a newer `agent_log.txt` entry reprioritizes them.

### Slice 1: Re-verify core tower behaviors
Status: `In Progress`

Targets:
- `OBJ-004`
- `OBJ-005`

What matters:
- `Basic`, `Seed`, and `Burst` must feel distinct.
- Seed launch must include a real travel phase before orb release.
- Upgrade tracks and readiness/cooldown reporting must remain accurate.

Primary files:
- `gridline/simulation.py`
- `gridline/app.py`
- `tests/test_simulation.py`

### Slice 2: Close power-tower behavior validation
Status: `In Progress`

Targets:
- `OBJ-006`

What matters:
- Funding must stay locked while power is active.
- The selected panel must report the active power state, not the suspended tower.
- The original tower must restore correctly after expiry or early destruction.

Primary files:
- `gridline/simulation.py`
- `gridline/app.py`
- `tests/test_simulation.py`

### Slice 3: Finish line-state conflict validation
Status: `In Progress`

Targets:
- `OBJ-007`
- `BUG-004`

What matters:
- Same-step red/green spread conflicts must preserve the current line color.
- Resolution must not depend on update order.

Primary files:
- `gridline/simulation.py`
- `tests/test_simulation.py`

### Slice 4: Finish Focus/visual pathing validation
Status: `In Progress`

Targets:
- `OBJ-008`
- `BUG-007`
- `BUG-008`

What matters:
- Focus Mode equal-angle ties must randomize correctly.
- Orb trails must follow actual traveled path through turns/intersections.
- Dense-combat readability must hold, not just isolated regression cases.

Primary files:
- `gridline/simulation.py`
- `gridline/app.py`
- `tests/test_simulation.py`

### Slice 5: End-to-end smoke and balance pass
Status: `Pending`

Targets:
- `OBJ-001`
- remaining feel and tuning review

What matters:
- `python main.py` should boot cleanly and stay stable.
- The current numeric defaults should be checked in actual play, not just in tests.
- Only tune values after a concrete observed issue.

Primary files:
- `main.py`
- `gridline/app.py`
- `gridline/spec.py`
- `game_config.json`

## Recommended Next Steps
If a coding agent starts fresh today, this is the shortest sensible path:

1. Read the latest `agent_log.txt` entries first.
2. Read the open items in `QA_TRACKER.md`.
3. Run `python -m pytest tests/test_simulation.py`.
4. Run `python main.py`.
5. Reproduce the oldest still-open `verify_fix` objective in live play.
6. Fix only the smallest unresolved slice that has direct evidence.
7. Update `QA_TRACKER.md` and `agent_log.txt` after the change lands.

## From-Scratch Rebuild Order
If the project had to be rebuilt from zero code, rebuild in this order:

1. `Spec + config loader`
   - Load approved defaults from `Game_Design.md`/`game_config.json`.
   - Keep numbers data-driven.
2. `Topology builder`
   - Generate large/medium/small grids with stable IDs and 12 perimeter hardpoints.
3. `Simulation core`
   - Fixed-step loop, currencies, timers, level progression, corruption threshold.
4. `Line-state system`
   - Blue/green/red line states, intensity growth, spread, and shared conflict arbitration.
5. `Tower system`
   - Base tower archetypes, firing cadence, upgrades, build flow, hardpoint occupancy.
6. `Orb system`
   - On-grid travel, continuous cleaning/harvesting, path history for trail rendering.
7. `Enemy system`
   - Seeder and striker movement, corruption creation, tower pressure, fallback targeting.
8. `Power tower system`
   - Funding chunks, stored charge, override state, suspension and restoration.
9. `UI + renderer`
   - Playfield rendering, readable line states, sidebar sections, selected-object details.
10. `Regression tests`
   - Lock down Seed travel, power override, spread arbitration, Focus ties, and UI eligibility.

## Coding Guardrails
- Do not reintroduce hardpoint activation unless the design docs change again.
- Do not treat readability cues as polish; they are part of gameplay clarity requirements.
- Keep archetype identity strong. Secondary modes are bounded flexibility, not role replacement.
- Keep topology identity separate from pixel layout so resize/fullscreen changes do not reset state.
- Prefer spec/config changes over hard-coded tuning.

## Definition Of Done For Current MVP
The MVP is in a clean coder-ready state when:

- All open `verify_fix` objectives in `QA_TRACKER.md` are moved to `pass`.
- `python -m pytest tests/test_simulation.py` passes.
- `python main.py` boots and plays without obvious runtime faults.
- Tower, orb, line-state, and enemy readability match the approved design behavior in motion.
- Any remaining issues are explicitly logged as deferred rather than accidental drift.
