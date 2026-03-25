# Gridline QA Tracker

## Purpose
This file tracks:

1. High-level testing objectives for the current MVP.
2. Specific bugs and implementation gaps that require coder action.
3. Clear pass criteria so features can move from exploratory testing to approval.

Use this file as the QA-facing working list. Use `agent_log.json` for formal cross-agent handoff entries and historical record.

## Status Legend
- `todo`: Not yet tested or not yet fixed.
- `in_progress`: Actively being tested or addressed.
- `blocked`: Cannot be validated yet due to another issue.
- `verify_fix`: Claimed fixed by coder; tester must re-run.
- `pass`: Tested and approved for current MVP scope.
- `wont_fix_mvp`: Known issue explicitly deferred out of MVP scope.

## Priority Legend
- `P0`: Blocks meaningful playtesting or breaks core rules.
- `P1`: Major design or gameplay mismatch; should be fixed before feature approval.
- `P2`: Important usability or readability issue; does not fully block testing.
- `P3`: Minor polish or follow-up item.

## Current Test Objectives
| ID | Objective | Scope | Current Status | Pass Criteria | Primary References |
| --- | --- | --- | --- | --- | --- |
| OBJ-001 | Launch and smoke-test playable MVP | App boot, run loop, quit, fullscreen, HUD visibility | `todo` | `python main.py` launches, remains stable, supports `Esc` quit and fullscreen toggle, no immediate runtime errors | `main.py`, `gridline/app.py`, `agent_log.json` |
| OBJ-002 | Validate topology and hardpoint layout | Grid generation, 12-hardpoint perimeter layout, selection readability | `pass` | Exactly 12 hardpoints appear with 3 per side and remain stable through a run | `gridline/topology.py`, `tests/test_simulation.py`, `Game_Design.md` sections `1`, `10` |
| OBJ-003 | Validate direct hardpoint build flow | Empty-hardpoint build gating, selected-state UI, no activation step | `pass` | Empty hardpoints are directly buildable when affordable, invalid actions are visibly disabled or explained, and no player-facing activation language remains | `gridline/app.py`, `gridline/simulation.py`, `Game_Design.md` sections `2`, `8` |
| OBJ-004 | Validate base tower behavior and upgrades | `Basic`, `Seed`, `Burst`, upgrade tracks, cooldown/readiness display | `partial` | Towers behave per archetype, all approved upgrade tracks are available, HUD reflects state accurately | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` sections `2A`-`2E`, `13`, `14` |
| OBJ-005 | Validate Seed Tower launch and landing model | Seed targeting, flight time, delayed release, landing behavior | `verify_fix` | Seed launch has real travel phase before orb release; landing obeys target resolution rules | `gridline/simulation.py`, `Game_Design.md` sections `2C`, `3A` |
| OBJ-006 | Validate power tower funding and override behavior | Funding lockout, active override stats, suspend/restore underlying tower | `verify_fix` | Funding is blocked during active deployment; selected panel reflects active power state; underlying tower restores correctly | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` section `7` |
| OBJ-007 | Validate line-state spread and conflict resolution | Red/green spread timing, intensity, same-step conflict arbitration | `verify_fix` | Same-step red/green conflicts preserve existing color regardless of call order | `gridline/simulation.py`, `Game_Design.md` section `4` |
| OBJ-008 | Validate Burst/Focus path rules and orb readability | Focus tie-break logic, path-faithful orb trail rendering, combat readability | `verify_fix` | Equal-angle Focus ties randomize correctly and orb trails stay on-grid through turns/intersections while fading from head to oldest tail segment | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` sections `2E`, `9` |
| OBJ-009 | Validate config-driven runtime values | `game_config.json` mapping into live runtime | `pass` | Visible config changes affect runtime consistently after relaunch | `gridline/spec.py`, `game_config.json`, `game_config_schema.json` |
| OBJ-010 | Validate regression test coverage for known risk areas | Automated coverage for critical gameplay behaviors | `pass` | Tests cover fixed Seed flight, power funding lockout, spread conflict resolution, Focus tie-breaks, and UI eligibility logic where practical | `tests/test_simulation.py`, `agent_log.json` |
| OBJ-011 | Validate gameplay readability cues | Enemy seeding telegraph, line-intensity readability, visible orb-impact feedback | `pass` | Corruption seeders darken before release and pulse on seeding, green/red line levels read light-to-dark by intensity, and meaningful orb state changes create an immediately visible line-feedback step | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` readability sections |
| OBJ-012 | Validate structured sidebar layout | Persistent status, contextual actions, utility separation, overflow reachability | `pass` | Status remains pinned, selection details stay visible, low-frequency controls live in a separate utility region, contextual actions swap by selection state, and the action region remains reachable without one long clipped button column | `gridline/app.py`, `Game_Design.md` sidebar layout sections |

## Active Bug Queue
| Bug ID | Priority | Feature | Status | Owner | Summary |
| --- | --- | --- | --- | --- | --- |
| BUG-001 | `P0` | Seed Tower launch model | `verify_fix` | Coder | Seed Tower currently skips in-flight seed travel and releases orb immediately at resolved target/start node. |
| BUG-002 | `P0` | Power tower funding rules | `pass` | Coder | Funding can continue while a power tower is already active, violating active-window lockout rules. |
| BUG-003 | `P1` | Power tower selected-state HUD | `pass` | Coder | Selected panel shows suspended underlying tower instead of active temporary power-state stats during override. |
| BUG-004 | `P0` | Red/green spread conflict resolution | `verify_fix` | Coder | Spread resolution is order-dependent because red and green mutate state in separate passes instead of a shared arbitration step. |
| BUG-005 | `P1` | Sidebar action affordance | `pass` | Coder | Invalid actions remain clickable and fail silently instead of being disabled or explained. |
| BUG-006 | `P1` | Missing upgrade tracks in UI | `pass` | Coder | Sidebar omits approved upgrade tracks and lacks current-value/next-value preview text. |
| BUG-007 | `P2` | Orb visual readability | `verify_fix` | Coder | Renderer draws orb heads only; expected trail/glow readability is missing. |
| BUG-008 | `P1` | Focus mode equal-angle tie behavior | `verify_fix` | Coder | Exact-angle ties collapse to adjacency/order instead of randomized tie-break before forward-bias selection. |
| BUG-009 | `P1` | Automated regression coverage gaps | `pass` | Coder | Current tests do not cover several known high-risk behaviors and can allow regression drift. |
| BUG-010 | `P1` | Corruption seeder telegraph direction | `pass` | Coder | Corruption seeders currently render darkest when farthest from seeding and become lighter as they approach release, opposite the approved readability rule. |

## Bug Details

### BUG-001: Seed Tower skips seed-in-flight phase
- Feature Tested: `Seed Tower` targeting, launch, flight, landing release
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P0`
- Coder Target:
  - `gridline/simulation.py:361`
  - `gridline/simulation.py:405`
  - `gridline/simulation.py:426`
  - `gridline/simulation.py:455`
- Bug Description: The current implementation resolves the target and spawns the orb as if the seed had already arrived. This removes the documented `launching_seed -> seed_in_flight -> landing_release` sequence and prevents line state from changing meaningfully during flight.
- Reproduction Steps:
  1. Launch the game and build a `Seed Tower`.
  2. Let it acquire a remote target.
  3. Observe the shot behavior at fire time.
  4. Compare the observed behavior against the design requirement for a visible or simulated travel phase before orb release.
- Expected vs. Actual Result:
  - Expected: A seed travels toward the selected target area first, then lands and releases the orb at the landing point after travel time.
  - Actual: The orb effectively starts at the resolved target/start node immediately, with no meaningful in-flight delay.
- QA Verification Notes:
  - Confirm that target line state can change during seed flight and that landing still resolves correctly.
  - Confirm Recall Mode still follows its local-defense targeting rules after the fix.

### BUG-002: Power funding is not locked during active deployment
- Feature Tested: Power tower funding and active-window restrictions
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P0`
- Coder Target:
  - `gridline/simulation.py:258`
  - `gridline/simulation.py:279`
- Bug Description: `fund_power()` allows additional funding while a power tower is already active because the logic only blocks on charge state or current funding percent, not active deployment state.
- Reproduction Steps:
  1. Accumulate enough coins to fully fund the power system.
  2. Deploy a power tower onto a hardpoint.
  3. While the power tower is active, attempt to buy more funding chunks.
- Expected vs. Actual Result:
  - Expected: Funding actions are blocked until the active power window fully ends.
  - Actual: Funding can continue during active deployment.
- QA Verification Notes:
  - Re-test both active and cooling/restored states.
  - Confirm the UI also prevents the invalid action, not just the simulation backend.

### BUG-003: Selected panel shows wrong object during power override
- Feature Tested: Power tower HUD/selection reporting
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py:281`
  - `gridline/simulation.py:287`
  - `gridline/simulation.py:785`
  - `gridline/simulation.py:793`
  - `gridline/app.py:138`
  - `gridline/app.py:167`
- Bug Description: When a powered hardpoint is selected, the sidebar reports the suspended permanent tower instead of the active temporary power-state entity. This hides the real HP, mode, and readiness values during the override window.
- Reproduction Steps:
  1. Build a permanent tower on a hardpoint.
  2. Fully fund and deploy a power tower onto that same hardpoint.
  3. Select the powered hardpoint while the override is active.
  4. Compare the displayed stats with the expected temporary power-state profile.
- Expected vs. Actual Result:
  - Expected: The selected panel reflects the active power tower state while the override is active.
  - Actual: The selected panel reflects the suspended underlying tower.
- QA Verification Notes:
  - After expiry or destruction, confirm the original tower returns with its prior state intact.

### BUG-004: Red/green spread conflicts are resolved by update order
- Feature Tested: Shared spread resolution and same-step conflict handling
- Status: `PARTIAL`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P0`
- Coder Target:
  - `gridline/simulation.py:796`
  - `gridline/simulation.py:840`
- Bug Description: Red and green spread are processed in separate passes/timers, so same-step conflicts depend on which color mutates the state first instead of a shared proposal-arbitration pass.
- Reproduction Steps:
  1. Set up or observe a state where red and green can both spread into the same target during the same resolution interval.
  2. Step the simulation through the spread event.
  3. Repeat enough times or under instrumented conditions to check whether result depends on processing order.
- Expected vs. Actual Result:
  - Expected: If red and green both target the same line in the same step, the target keeps its existing color.
  - Actual: Result depends on update order/timer alignment.
- QA Verification Notes:
  - Verify both visible behavior and automated tests after the fix.
  - Confirm no regression to single-color spread rates or intensity growth.

### BUG-005: Sidebar leaves invalid actions clickable
- Feature Tested: Build/upgrade/purchase affordance and player feedback
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `gridline/app.py:41`
  - `gridline/app.py:89`
  - `gridline/app.py:123`
  - `gridline/app.py:167`
- Bug Description: Action buttons remain clickable even when the selected state, affordability, or eligibility does not permit the action. Failures are handled silently in the simulation layer instead of being prevented or explained in the UI.
- Reproduction Steps:
  1. Select an object/state where one or more actions should be invalid.
  2. Attempt activation, build, upgrade, behavior purchase, or swap without satisfying the required condition.
  3. Observe button availability and player-facing feedback.
- Expected vs. Actual Result:
  - Expected: Invalid actions are disabled or clearly labeled with the reason they cannot be used.
  - Actual: Buttons remain clickable and the action fails silently.
- QA Verification Notes:
  - Validate selection-state gating, affordability gating, tower-presence gating, and cooldown gating separately.

### BUG-006: Sidebar is missing approved upgrade tracks and preview text
- Feature Tested: Upgrade panel completeness and readability
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `gridline/app.py:123`
  - `gridline/app.py:167`
- Bug Description: The panel currently exposes only `fire_rate`, `hit_damage`, and `grid_access_tier`. Approved MVP tracks also include `hp`, `snake_speed`, and `shot_range`, and the UI does not preview current value versus next value before purchase.
- Reproduction Steps:
  1. Build each tower archetype.
  2. Select the tower and inspect the upgrade area.
  3. Compare available upgrades and displayed information against the approved design.
- Expected vs. Actual Result:
  - Expected: All approved upgrade tracks are present where applicable, with clear cost and current-to-next-value preview text.
  - Actual: Several tracks are missing and preview information is incomplete.
- QA Verification Notes:
  - Re-check shot-range applicability for archetypes/modes where range meaningfully applies.

### BUG-007: Orbs lack trail rendering
- Feature Tested: Orb readability and rendering fidelity
- Status: `PARTIAL`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P2`
- Coder Target:
  - `gridline/app.py:169`
  - `gridline/app.py:202`
- Bug Description: The renderer currently draws orb heads only. The design expects visible trail/glow support so orb motion is readable during action.
- Reproduction Steps:
  1. Launch the game and create enough activity to observe several orbs in motion.
  2. Watch moving orbs against the line network during combat.
- Expected vs. Actual Result:
  - Expected: Orb heads and trails make travel direction and persistence readable.
  - Actual: Only orb heads are drawn.
- QA Verification Notes:
  - Re-test readability under dense action, not just isolated shots.

### BUG-008: Focus Mode tie-breaks are not randomized correctly
- Feature Tested: `Burst Tower / Focus Mode` path selection
- Status: `PARTIAL`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py:594`
  - `gridline/simulation.py:599`
- Bug Description: The current Focus Mode implementation sorts exits and takes the first two rather than explicitly randomizing equal-angle ties before applying the `0.70 / 0.30` forward-bias selection. Exact-angle ties therefore collapse to adjacency/order artifacts.
- Reproduction Steps:
  1. Build a `Burst Tower` and unlock `Focus Mode`.
  2. Force or observe a movement choice at an intersection with exact-angle tie candidates.
  3. Repeat enough times to check whether tie behavior is randomized before weighted forward selection.
- Expected vs. Actual Result:
  - Expected: Equal-angle ties are randomized first, then the documented forward-bias rule is applied.
  - Actual: Candidate order is effectively deterministic from sorting/adjacency order.
- QA Verification Notes:
  - This should be verified with automated coverage in addition to manual observation.

### BUG-009: Regression coverage is too thin for current risk areas
- Feature Tested: Automated test coverage for high-risk behavior
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `tests/test_simulation.py`
- Bug Description: The current automated checks do not cover several already-known failure areas, which means core behavior can regress without detection.
- Missing Coverage Targets:
  - Delayed `Seed Tower` landing and release.
  - Power-funding lockout while active.
  - Power-state HUD/selected-object reporting.
  - Shared red/green spread conflict resolution.
  - Sidebar eligibility/disabled-action behavior where testable.
  - `Focus Mode` equal-angle tie handling.
- Expected vs. Actual Result:
  - Expected: High-risk systems have targeted regression coverage.
  - Actual: Coverage is limited to a small subset of current functionality.
- QA Verification Notes:
  - Treat this as required support work for closing the related bugs above.

### BUG-010: Corruption seeder telegraphing darkens in the wrong direction
- Feature Tested: Corruption seeder pre-seed telegraph readability
- Status: `PASS`
- Source: `planner-20260325-004`, `designer-20260325-004`, and `coder-20260325-005` in `agent_log.json`
- Priority: `P1`
- Coder Target:
  - `gridline/app.py:134`
  - `gridline/app.py:139`
- Bug Description: The current `enemy_render_color()` logic makes corruption seeders start dark and become lighter as seeding approaches. The approved gameplay-readability contract requires the opposite progression: lighter red earlier, darker red closer to release, then a pulse/burst when corruption is seeded.
- Reproduction Steps:
  1. Sample a corruption seeder's render color with full `path_budget_remaining`.
  2. Sample the color again with near-zero `path_budget_remaining`.
  3. Compare the color progression against the planner/designer requirement.
- Expected vs. Actual Result:
  - Expected: The enemy starts lighter and darkens as the seeding moment approaches.
  - Actual: The enemy starts darker and becomes lighter as the seeding moment approaches.
- QA Verification Notes:
  - The pulse-on-seed effect appears present; the issue is the countdown telegraph direction before release.

## Next QA Sequence
1. Re-run smoke and interaction testing after the next coder pass.
2. Move any coder-claimed fixes from `todo` to `verify_fix`.
3. Re-test each bug against the explicit expected result in this file.
4. When a bug passes, add a formal approval or bug-resolution entry to `agent_log.json`.

## File Maintenance Rules
- Add new bugs under `Active Bug Queue` first, then create a detailed entry if coder action is needed.
- Keep bug IDs stable even if wording changes.
- Update status here before writing the formal `agent_log.json` entry so the working queue stays current.
- Do not mark `pass` unless the behavior has been re-tested after the relevant code change.
