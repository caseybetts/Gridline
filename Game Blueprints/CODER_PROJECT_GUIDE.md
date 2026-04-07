# Gridline Coder Project Guide

## Purpose
Use this file as the coder-facing bootstrap and reconstruction guide.
It should give a future coding agent enough durable context to understand how the project is built without rediscovering the codebase from scratch.
It should remain state-agnostic. Live priorities, active bugs, and recent work belong in `CURRENT_HANDOFFS.md`, `QA_TRACKER.md`, and `agent_log.txt`, not here.

## Source Of Truth Escalation Order
Do not read every source below before changing code.
Start with the prompt, repo doc guide, and current handoff, then expand only if the active task is not fully scoped.

1. `Coder_Prompt.md`
2. `REPO_DOC_GUIDELINES.md`
3. `CURRENT_HANDOFFS.md`
4. implementation brief or exact files/tests named in the inbox
5. relevant `QA_TRACKER.md` entry
6. relevant `Game_Design.md` section
7. `game_summary.md` if product intent is unclear
8. `CODER_PROJECT_GUIDE.md` when architecture or rebuild context is needed
9. `agent_log.txt` if chronology matters

Rules:
- `game_summary.md` is the planner-owned product vision.
- `Game_Design.md` is the detailed coder spec and numeric baseline.
- `REPO_DOC_GUIDELINES.md` defines what belongs in which repo document.
- `CURRENT_HANDOFFS.md` is the live role mailbox and sequencing board.
- `QA_TRACKER.md` is the live validation queue, not the design source.
- `agent_log.txt` is the recent chronology of meaningful work batches.

## Project Objective
Build a playable endless-survival, line-based tower defense where the player contains corruption on a three-tier glowing grid by building edge hardpoint towers, managing upgrades, and using readable, path-faithful orb behavior.

The MVP must preserve these non-negotiables:
- Gameplay happens on grid lines and intersections, not inside cells.
- The three base towers are `Basic Tower`, `Seed Tower`, and `Burst Tower`.
- Each tower keeps a strong archetype identity and may buy exactly one mapped secondary mode.
- Corruption is the primary fail state. The run ends when corruption exceeds the configured percentage.
- Orbs, enemy telegraphs, and line-state changes must be readable in motion.
- Orbs leave fading trails and should support a sleek technical presentation.

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

## Live State Lives Elsewhere
Use these files for the project's current state:

- `CURRENT_HANDOFFS.md` for the active role mailbox and next-step sequencing.
- `QA_TRACKER.md` for open objectives, open bugs, and verification status.
- `agent_log.txt` for recent chronology and landed work order.

This guide should not duplicate live backlog, sprint status, or recently completed work.

## From-Scratch Rebuild Order
If the project had to be rebuilt from zero code, rebuild in this order:

1. `Spec + config loader`
   - Load approved defaults from `Game_Design.md` and `game_config.json`.
   - Keep numbers data-driven.
2. `Topology builder`
   - Generate large, medium, and small grids with stable IDs and perimeter hardpoints.
3. `Simulation core`
   - Fixed-step loop, currencies, timers, level progression, and corruption threshold.
4. `Line-state system`
   - Blue, green, and red line states, intensity growth, spread, and shared conflict arbitration.
5. `Tower system`
   - Base tower archetypes, firing cadence, upgrades, build flow, and hardpoint occupancy.
6. `Orb system`
   - On-grid travel, continuous cleaning and harvesting, and path history for trail rendering.
7. `Enemy system`
   - Seeder and striker movement, corruption creation, tower pressure, and fallback targeting.
8. `Power tower system`
   - Funding chunks, stored charge, override state, suspension, and restoration.
9. `UI + renderer`
   - Playfield rendering, readable line states, sidebar sections, and selected-object details.
10. `Regression tests`
   - Lock down seed travel, power override, spread arbitration, Focus ties, and UI eligibility.

## Implementation Notes
- Keep topology identity separate from pixel layout so resize and fullscreen changes do not reset gameplay state.
- Prefer config/spec changes over hard-coded tuning.
- Keep simulation rules in `gridline/simulation.py` and config/spec interpretation in `gridline/spec.py`.
- Treat `tests/test_simulation.py` as the main regression surface for high-risk gameplay and UI invariants.
- Preserve clean separation between game-state logic and presentation logic so the project remains rebuildable and testable.

## Coding Guardrails
- Do not reintroduce hardpoint activation unless the design docs change again.
- Do not treat readability cues as polish; they are part of gameplay clarity requirements.
- Keep archetype identity strong. Secondary modes are bounded flexibility, not role replacement.
- Keep topology identity separate from pixel layout so resize/fullscreen changes do not reset state.
- Prefer spec/config changes over hard-coded tuning.
