# Gridline QA Tracker

## Purpose
This file tracks:

1. High-level testing objectives for the current MVP.
2. Specific bugs and implementation gaps that require coder action.
3. Clear pass criteria so features can move from exploratory testing to approval.

Use this file as the QA-facing working list. Use `agent_log.txt` for formal cross-agent handoff entries and historical record.

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
| OBJ-001 | Launch and smoke-test playable MVP | App boot, run loop, quit, fullscreen, HUD visibility | `pass` | `python main.py` launches, remains stable, supports `Esc` quit and fullscreen toggle, no immediate runtime errors | `main.py`, `gridline/app.py`, `agent_log.txt` |
| OBJ-002 | Validate topology and hardpoint layout | Grid generation, 12-hardpoint perimeter layout, selection readability | `pass` | Exactly 12 hardpoints appear with 3 per side and remain stable through a run | `gridline/topology.py`, `tests/test_simulation.py`, `Game_Design.md` sections `1`, `10` |
| OBJ-003 | Validate direct hardpoint build flow | Empty-hardpoint build gating, selected-state UI, no activation step | `pass` | Empty hardpoints are directly buildable when affordable, invalid actions are visibly disabled or explained, and no player-facing activation language remains | `gridline/app.py`, `gridline/simulation.py`, `Game_Design.md` sections `2`, `8` |
| OBJ-004 | Validate base tower behavior and upgrades | `Basic`, `Seed`, `Burst`, upgrade tracks, cooldown/readiness display | `pass` | Towers behave per archetype, all approved upgrade tracks are available, HUD reflects state accurately | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` sections `2A`-`2E`, `13`, `14` |
| OBJ-005 | Validate Seed Tower launch and landing model | Seed targeting, flight time, delayed release, landing behavior | `pass` | Seed launch has real travel phase before orb release; landing obeys target resolution rules | `gridline/simulation.py`, `Game_Design.md` sections `2C`, `3A` |
| OBJ-006 | Validate power tower funding and override behavior | Funding lockout, active override stats, suspend/restore underlying tower | `pass` | Funding is blocked during active deployment; selected panel reflects active power state; underlying tower restores correctly | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` section `7` |
| OBJ-007 | Validate line-state spread and conflict resolution | Red/green spread timing, intensity, same-step conflict arbitration | `pass` | Same-step red/green conflicts preserve existing color regardless of call order | `gridline/simulation.py`, `Game_Design.md` section `4` |
| OBJ-008 | Validate Burst/Focus path rules and orb readability | Focus tie-break logic, path-faithful orb trail rendering, combat readability | `pass` | Equal-angle Focus ties randomize correctly and orb trails stay on-grid through turns/intersections while fading from head to oldest tail segment | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` sections `2E`, `9` |
| OBJ-009 | Validate config-driven runtime values | `game_config.json` mapping into live runtime | `pass` | Visible config changes affect runtime consistently after relaunch | `gridline/spec.py`, `game_config.json`, `game_config_schema.json` |
| OBJ-010 | Validate regression test coverage for known risk areas | Automated coverage for critical gameplay behaviors | `pass` | Tests cover fixed Seed flight, power funding lockout, spread conflict resolution, Focus tie-breaks, and UI eligibility logic where practical | `tests/test_simulation.py`, `agent_log.txt` |
| OBJ-011 | Validate gameplay readability cues | Enemy seeding telegraph, line-intensity readability, visible orb-impact feedback | `pass` | Corruption seeders darken before release and pulse on seeding, green/red line levels read light-to-dark by intensity, and meaningful orb state changes create an immediately visible line-feedback step | `gridline/simulation.py`, `gridline/app.py`, `Game_Design.md` readability sections |
| OBJ-012 | Validate structured sidebar layout | Persistent status, contextual actions, utility separation, overflow reachability | `pass` | Status remains pinned, selection details stay visible, low-frequency controls live in a separate utility region, contextual actions swap by selection state, and the action region remains reachable without one long clipped button column | `gridline/app.py`, `Game_Design.md` sidebar layout sections |
| OBJ-013 | Evaluate post-MVP run pacing and economy pressure | Section 20 live-play evidence for survival target, opener pressure, and early spending flexibility | `blocked` | In informed non-throw play, most losses land inside the 10 to 15 minute target band; repeated losses before minute 5 are exceptional; early experiments do not instantly collapse the run | `game_summary.md` current milestone, `Game_Design.md` section `20`, `agent_log.txt` |
| OBJ-014 | Evaluate post-MVP role separation and late-use systems | Tower-role clarity, secondary-mode usefulness, power-tower usage, and remaining readability/usability friction in longer sessions | `blocked` | Sessions last long enough to judge archetype separation, secondary-mode tradeoffs, power-tower usage, and late-run readability without opener collapse dominating the result | `game_summary.md` current milestone, `Game_Design.md` section `20`, `agent_log.txt` |
| OBJ-015 | Validate playtester-followup usability, feedback, and interior-influence pass | Empty-hardpoint build reachability, attributed harvest/economy feedback, and default `Basic Tower` / `Seed Tower` interior influence | `pass` | Selecting an empty hardpoint resets the contextual action region to the build controls, real orb/harvest results create immediate local feedback plus attributable recent-income telemetry, and default `Basic Tower` / `Seed Tower` output visibly favors interior lines from edge hardpoints without breaking the minute-2 checkpoint regression | `gridline/app.py`, `gridline/simulation.py`, `tests/test_simulation.py`, `Game_Design.md` sections `3B`, `4`, `5`, `8` |
| OBJ-016 | Validate config-agnostic HUD and sidebar readability pass | Relative status bars/badges, in-place disabled-action reasons, compact action labels, and success feedback under variable config values | `pass` | At the minimum supported window, run-critical status keeps a stable scan order, power/corruption state remains legible through text-plus-bar treatment, unavailable actions show concise in-place reasons, and successful funding/mode/build actions emit immediate readable feedback without relying on fixed balance assumptions | `gridline/app.py`, `tests/test_simulation.py`, `Game_Design.md` section `8A` |
| OBJ-017 | Validate stable grouped controls and directional corruption-reduction cues | Stationary grouped action shells, concise multi-column labels, and cleaner orb-to-corruption cause-and-effect readability | `pass` | At the minimum supported window, grouped action shells stay visually stationary through normal selection changes, compact labels keep primary action meaning readable under wide value ranges, and orb-driven red/green reductions read as calming/cleaning events rather than generic flashes | `gridline/app.py`, `gridline/simulation.py`, `tests/test_simulation.py`, `Game_Design.md` sections `4`, `8`, `8A` |

## Active Bug Queue
| Bug ID | Priority | Feature | Status | Owner | Summary |
| --- | --- | --- | --- | --- | --- |
| BUG-001 | `P0` | Seed Tower launch model | `pass` | Coder | Seed target resolution now snaps to emit-capable landing nodes so both default Seed and `Recall Mode` release an orb reliably after flight. |
| BUG-002 | `P0` | Power tower funding rules | `pass` | Coder | Funding can continue while a power tower is already active, violating active-window lockout rules. |
| BUG-003 | `P1` | Power tower selected-state HUD | `pass` | Coder | Selected panel shows suspended underlying tower instead of active temporary power-state stats during override. |
| BUG-004 | `P0` | Red/green spread conflict resolution | `pass` | Coder | Same-step red/green spread now preserves the target's existing color and no longer depends on update order. |
| BUG-005 | `P1` | Sidebar action affordance | `pass` | Coder | Invalid actions remain clickable and fail silently instead of being disabled or explained. |
| BUG-006 | `P1` | Missing upgrade tracks in UI | `pass` | Coder | Sidebar omits approved upgrade tracks and lacks current-value/next-value preview text. |
| BUG-007 | `P2` | Orb visual readability | `pass` | Coder | Renderer now produces path-faithful orb trails that stay on-grid through turns and fade from head to tail. |
| BUG-008 | `P1` | Focus mode equal-angle tie behavior | `pass` | Coder | Equal-angle Focus candidates now randomize before the forward-bias pick and no longer collapse to a fixed adjacency order. |
| BUG-009 | `P1` | Automated regression coverage gaps | `pass` | Coder | Current tests do not cover several known high-risk behaviors and can allow regression drift. |
| BUG-010 | `P1` | Corruption seeder telegraph direction | `pass` | Coder | Corruption seeders currently render darkest when farthest from seeding and become lighter as they approach release, opposite the approved readability rule. |
| BUG-011 | `P1` | Power tower suspended-state restoration | `pass` | Coder | Suspended towers now freeze their cooldown-backed readiness state during power override so restoration can return the pre-power timings intact. |
| BUG-012 | `P2` | Secondary mode UI naming | `pass` | Coder | Sidebar mode text and action labels now use explicit fixed mode names instead of generic `secondary` wording. |
| BUG-013 | `P0` | Post-MVP opener pressure and pacing | `pass` | Coder | The opener-stabilization pass no longer collapses informed openers in seconds and restores the minute-2 checkpoint as a reachable evaluation gate. |
| BUG-014 | `P1` | Secondary-mode and power-tower practical viability | `pass` | Coder | Live-config tuning now reaches real charge/deploy windows in sampled `secondary-first`, `mixed-then-power`, and `direct power-rush` runs while the minute-two checkpoint regression still passes. |
| BUG-015 | `P1` | Empty-hardpoint build-control reachability | `pass` | Coder | Selecting an empty hardpoint now resets the contextual action region back to the build controls so tower choices do not stay hidden below the prior scroll offset. |
| BUG-016 | `P1` | Orb-impact, harvest-result, and economy attribution feedback | `pass` | Coder | Real green/red line-state steps now pair the existing line flash with local `+coins` harvest popups, a recent-harvest HUD line, and selected-tower economy telemetry so testers can tell what income was earned and by which tower behavior. |
| BUG-017 | `P1` | Default edge-tower interior influence | `pass` | Coder | Default `Basic Tower` and `Seed Tower` output now applies interior-favoring turn/target rules from edge hardpoints so they stop settling into persistent perimeter-only coverage. |
| BUG-018 | `P1` | Grouped action-shell stability | `pass` | Coder | The selection panel now uses a stable height budget and fixed button line count so the grouped action shells stay visually stationary through normal selection changes at the minimum supported window. |
| BUG-019 | `P1` | Section 20 role separation and late-use value | `pass` | Coder | The stabilized live config now clears the focused late-use guard suite, mixed and delayed seeded follow-ups both hit `100%` funding with real deploys across seeds `1`, `7`, and `13`, and direct power-rush still tops out at `70%` funding with no deploy across those seeds. |
| BUG-020 | `P3` | Playfield bounds framing | `pass` | Coder | The dedicated board surface/frame now terminates exactly at `topology.playfield_rect`, and the surrounding canvas reads as darker background instead of extra playable grid. |
| BUG-021 | `P2` | Supported-window control reachability | `pass` | Coder | At the supported `1280x720` floor, pinned sidebar regions plus internal detail overflow and occupied-selection resets keep the first tower-control row visible and the action region reachable. |
| BUG-022 | `P0` | Ready-shell start control visibility | `pass` | Coder | Ready-shell status rows now collapse to a startup-safe subset and the sidebar reserves visible utility space so the `Start Run` control stays mapped and reachable at the default `1280x720` launch size. |
| BUG-023 | `P1` | Section 20 pacing and power-tower role | `wont_fix_mvp` | Coder | Deferred from the current MVP path; the power tower is now treated as a non-core supplemental mechanic and its tuning should not block GUI, shell, or core-mechanics completion. |

## Bug Details

### BUG-001: Seed Tower skips seed-in-flight phase
- Feature Tested: `Seed Tower` targeting, launch, flight, landing release
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
- Priority: `P0`
- Coder Target:
  - `gridline/simulation.py:361`
  - `gridline/simulation.py:405`
  - `gridline/simulation.py:426`
  - `gridline/simulation.py:455`
- Bug Description: The current implementation now includes a real `seed_in_flight` phase, but landing resolution still fails for some validly selected targets because the targeting pool includes intersections that do not have a legal outgoing segment for the tower's current traversal tier on landing.
- Reproduction Steps:
  1. Launch the game and build a `Seed Tower`.
  2. Let it acquire and fire at multiple valid in-range targets, or instrument target selection to pick a medium/small intersection that has no legal `large`-tier exit for the current tower access tier.
  3. Wait for each seed flight to finish.
  4. Observe whether an orb is released at the landing point.
  5. Repeat after purchasing and activating `Recall Mode`.
- Expected vs. Actual Result:
  - Expected: A seed travels toward the selected target area first, then always lands and releases the orb at a valid landing point after travel time.
  - Actual: Re-test confirmed the fix. `python -m pytest tests/test_simulation.py -q` now passes new regressions that exercise both default Seed mode and `Recall Mode` across repeated launches, and each completed seed flight releases an orb at landing.
- QA Verification Notes:
  - The verified implementation resolves landing targets onto emit-capable nodes before launch while preserving the delayed in-flight phase.
  - This closes both the original default Seed failure and the later `Recall Mode` edge case.

### BUG-002: Power funding is not locked during active deployment
- Feature Tested: Power tower funding and active-window restrictions
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
- Source: `designer-20260324-012` in `agent_log.txt`
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
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
  - Actual: Re-test confirmed that same-step conflicts preserve the existing color for blue, red, and green targets, while single-color spread and intensity growth still occur normally.
- QA Verification Notes:
  - Automated coverage in `tests/test_simulation.py` passes.
  - Targeted retest with forced spread rolls confirmed conflict preservation and continued red-only growth behavior.

### BUG-005: Sidebar leaves invalid actions clickable
- Feature Tested: Build/upgrade/purchase affordance and player feedback
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
- Source: `designer-20260324-012` in `agent_log.txt`
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
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
  - Actual: Re-test confirmed multi-segment trail rendering, on-grid trail continuity through turns/intersections, and head-to-tail fade support in the helper/rendering path.
- QA Verification Notes:
  - Automated coverage now exercises both multi-segment trail point reconstruction and fade ordering.
  - Dense live-combat readability still merits future eyeball tuning, but the missing-trail defect itself is resolved for MVP verification scope.

### BUG-008: Focus Mode tie-breaks are not randomized correctly
- Feature Tested: `Burst Tower / Focus Mode` path selection
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
  - Actual: Re-test confirmed that equal-angle ties can produce different second-choice branches before the forward-bias selection is applied, matching the approved rule.
- QA Verification Notes:
  - Automated coverage in `tests/test_simulation.py` now exercises the equal-angle tie behavior.
  - Targeted deterministic retests produced both tied side branches under controlled random sequences.

### BUG-009: Regression coverage is too thin for current risk areas
- Feature Tested: Automated test coverage for high-risk behavior
- Status: `PASS`
- Source: `designer-20260324-012` in `agent_log.txt`
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
- Source: `planner-20260325-004`, `designer-20260325-004`, and `coder-20260325-005` in `agent_log.txt`
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

### BUG-011: Suspended tower cooldown does not restore intact after power override
- Feature Tested: `Power Tower` override restoration behavior
- Status: `PASS`
- Source: tester verification against `Game_Design.md` section `7`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py`
- Bug Description: A permanent tower suspended under power override continued advancing its cooldown timers while the power tower was active, so the restored tower did not return in its full pre-power readiness state.
- Reproduction Steps:
  1. Build a tower on a hardpoint.
  2. Put that tower on a non-zero fire cooldown, and optionally a non-zero swap cooldown.
  3. Fully charge and deploy the power tower onto that occupied hardpoint.
  4. Wait for the power window to expire.
  5. Compare the restored tower's cooldown/readiness state with the values it had at the moment of deployment.
- Expected vs. Actual Result:
  - Expected: The underlying tower returns with its pre-power state intact, including readiness and cooldown state.
  - Actual: Re-test confirmed the fix. The suspended tower's fire and swap cooldown values remain unchanged across a full power-override window and restore intact when the power state ends.
- QA Verification Notes:
  - Funding lockout and active selected-object reporting remain correct.
  - The regression suite now covers the restored cooldown values directly.

### BUG-012: Sidebar uses generic secondary-mode naming
- Feature Tested: Secondary-mode HUD and action labeling
- Status: `PASS`
- Source: tester verification against `Game_Design.md` sections `2D` and `2E`
- Priority: `P2`
- Coder Target:
  - `gridline/app.py`
  - `gridline/simulation.py`
- Bug Description: The sidebar reported generic secondary-mode wording such as `Mode: secondary`, `Buy Secondary`, and `Swap Mode` instead of the explicit approved mode names `Guard Mode`, `Recall Mode`, and `Focus Mode`.
- Reproduction Steps:
  1. Build any tower with a fixed secondary behavior.
  2. Purchase its secondary mode.
  3. Toggle into that mode.
  4. Inspect the selected-object text and related action labels in the sidebar.
- Expected vs. Actual Result:
  - Expected: The selected panel and actions use explicit named mode labels for the active archetype.
  - Actual: Re-test confirmed the fix. The selected-object panel now shows explicit mode names such as `Recall Mode`, and the contextual action labels use named wording such as `Buy Recall Mode` and `Switch to Default Mode`.
- QA Verification Notes:
  - Automated regression now checks `Recall Mode` naming in both the selected-object text and the sidebar action labels.
  - This closes the remaining HUD signoff blocker for `OBJ-004`.

### BUG-013: Post-MVP opener pressure collapses far below the Section 20 target band
- Feature Tested: Section 20 run pacing and economy pressure
- Status: `PASS`
- Source: tester live-play evaluation against `game_summary.md` current milestone and `Game_Design.md` section `20`
- Priority: `P0`
- Coder Target:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`
- Bug Description: The current post-MVP build failed the first tuning lane before later systems could be meaningfully evaluated. Across informed scripted play sessions, the run ended in seconds rather than minutes, massively below the required Section 20 pacing floor.
- Reproduction Steps:
  1. Start a fresh run on the current build.
  2. Use any informed opener such as a mixed three-tower start, a basic-only start, or an upgrade-first start.
  3. Continue making reasonable build/upgrade decisions without intentionally stalling.
  4. Record `run_duration` and compare it to the Section 20 target band.
- Expected vs. Actual Result:
  - Expected: In informed non-throw play, most losses should land inside the `10` to `15` minute target band, and repeated losses before minute `5` should be exceptional.
  - Actual: Re-test confirmed the opener-stabilization gate. Repeated checkpoint regression runs passed, and standalone informed opener retests now survive to `120.03` to `128.03` seconds instead of the prior `12.0` to `14.3` second collapse band.
- QA Verification Notes:
  - `python -m pytest tests/test_simulation.py -q -k minute_two` passed in five consecutive reruns after one initial inconsistent invocation.
  - Standalone retests of the same `basic_only`, `mixed_three`, and `upgrade_first` opener styles finished at `120.03` or `128.03` seconds.
  - This closes the emergency opener-collapse blocker, but the broader Section 20 pacing target remains under `OBJ-013`.

### BUG-014: Secondary modes and the power tower are strategically non-viable under the current opener
- Feature Tested: Section 20 secondary-mode tradeoffs and power-tower usage
- Status: `PASS`
- Source: tester live-play evaluation against `game_summary.md` current milestone and `Game_Design.md` section `20`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`
- Bug Description: The reopened Section 20 lane now allows meaningful secondary-mode testing, but the power tower still does not become practically reachable or usable during reasonable early-to-mid runs, and the broader late-run judgment window remains short.
- Reproduction Steps:
  1. Start a fresh run.
  2. Try an informed secondary-first opener such as `Basic Tower -> Guard Mode`, or a power-rush opener that buys early power funding chunks after the first tower.
  3. Continue making reasonable follow-up choices.
  4. Compare the resulting run duration and system usage against a more board-stabilizing opener.
- Expected vs. Actual Result:
  - Expected: Secondary modes should offer meaningful situational tradeoffs, and the power tower should function as an emergency stabilizer that becomes meaningfully usable during longer runs.
- Actual: Re-test confirmed the practical-viability fix. Direct execution of the live-config regression functions passed for both the minute-two checkpoint and the deterministic power-window check, and sampled `secondary-first`, `mixed-then-power`, and `direct power-rush` runs each reached `100%` funding plus one real deploy before loss or the local time cap.
- QA Verification Notes:
  - Directly invoked `test_live_config_opener_styles_reach_the_minute_two_checkpoint_window()` and `test_live_config_power_rush_can_reach_a_real_power_deploy_window()` from `tests/test_simulation.py` because `pytest` is not installed in the default interpreter in this workspace.
  - Sampled deterministic runs with seeds `1`, `7`, and `13` all reached a real power deploy in the three named styles; observed run durations ranged from `120.03` to `144.03` seconds for most losses, with one `mixed-then-power` sample reaching the local `240.03` second cap.
  - `Guard Mode` activation remained reachable in the sampled `secondary-first` line, and the minute-two checkpoint remained intact after the economy and power-funding changes.
  - This closes `BUG-014`, but the broader Section 20 pacing and longer-session evaluation gates remain open under `OBJ-013` and `OBJ-014`.

### BUG-015: Empty hardpoint selection can leave build controls below the current scroll offset
- Feature Tested: Sidebar contextual-action reachability
- Status: `PASS`
- Source: planner/designer triage of `Play_Tester_Notes.md`
- Priority: `P1`
- Coder Target:
  - `gridline/app.py`
  - `tests/test_simulation.py`
- Bug Description: After the sidebar has been scrolled while a tower is selected, choosing an empty hardpoint can leave the build actions below the retained scroll offset. The build controls exist, but they are not immediately reachable.
- Reproduction Steps:
  1. Select a tower with enough contextual controls to scroll the action region.
  2. Scroll the action region downward.
  3. Select an empty hardpoint.
  4. Check whether the build controls are immediately visible without additional scrolling.
- Expected vs. Actual Result:
  - Expected: Selecting an empty hardpoint resets the contextual action region to the build group so the build buttons are immediately visible.
  - Actual: Re-test confirmed the fix in both the default view and a constrained live-config window. Empty-hardpoint selection resets the action region to the build group and forces the scroll position back to the top.
- QA Verification Notes:
  - Runtime probe confirmed the build action group repacks immediately after selecting an empty hardpoint.
  - Constrained-window verification at `900x520` still triggered the reset path.

### BUG-016: Harvest results and economy contribution are still too opaque during playtesting
- Feature Tested: Orb-impact readability, harvest-result feedback, and tester-facing economy clarity
- Status: `PASS`
- Source: planner/designer triage of `Play_Tester_Notes.md`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py`
  - `gridline/app.py`
  - `tests/test_simulation.py`
- Bug Description: Testers could not reliably tell when an orb had actually stepped down a line state, what harvest income had just been earned, or which tower behavior was producing the income.
- Reproduction Steps:
  1. Launch a run and build at least one tower that can harvest green lines.
  2. Watch orb interactions against both red and green lines during live play.
  3. When harvest income occurs, inspect the local playfield cue, recent-harvest HUD line, and selected-tower details.
  4. Compare whether the tester can now attribute recent income and compare tower economy behavior without guesswork.
- Expected vs. Actual Result:
  - Expected: Real line-state drops remain visibly flashed, harvest income creates a local `+coins` cue near the affected segment, the HUD reports the latest harvest event, and the selected-tower panel exposes shot-cost plus harvest-relevant output and recent income.
  - Actual: Re-test confirmed the new feedback chain on a real harvest event. The live-config runtime produced a local `+4c` popup, a matching recent-harvest HUD entry, and selected-tower economy telemetry showing `Recent +4c / 6s` for the firing `Basic Tower`.
- QA Verification Notes:
  - The event remained tied to a real green-line harvest threshold crossing rather than a no-op contact.
  - No-selection and selected-tower text both exposed the recent-income attribution clearly enough to identify the responsible tower and mode.

### BUG-017: Default Basic and Seed output still reads as perimeter-hugging instead of interior-reaching
- Feature Tested: Default `Basic Tower` and default `Seed Tower` edge-origin influence
- Status: `PASS`
- Source: planner/designer triage of `Play_Tester_Notes.md`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py`
  - `tests/test_simulation.py`
- Bug Description: Playtest evidence showed `Basic Tower` often cleaning along the wall and `Seed Tower` repeatedly launching into one direction, undermining the intended edge-hardpoint-to-interior containment fantasy.
- Reproduction Steps:
  1. Start a run and build default `Basic Tower` and default `Seed Tower` on edge hardpoints.
  2. Observe several shots from each while they remain in default mode.
  3. Check whether default `Basic Tower` takes inward turns from edge-origin travel and whether default `Seed Tower` preferentially chooses interior-capable launch targets and landing exits when available.
  4. Compare the result against the prior perimeter-skimming behavior.
- Expected vs. Actual Result:
  - Expected: Default `Basic Tower` and `Seed Tower` should visibly influence interior lines from edge hardpoints instead of collapsing into one perimeter lane whenever a legal inward route exists.
  - Actual: Re-test confirmed the new interior bias in live-config probes. Default `Seed Tower` repeatedly selected interior-preferred targets from a top-edge hardpoint, and default `Basic Tower` chose the first eligible inward turn from top-edge travel instead of continuing to skim the perimeter.
- QA Verification Notes:
  - `python -m pytest tests/test_simulation.py -q -k minute_two` passed in three consecutive reruns after the pathing change.
  - `Guard Mode` and `Recall Mode` remain intentionally local; the verified improvement is specific to the default modes.

### BUG-018: Grouped action shells still shift vertically when selection details grow
- Feature Tested: Stationary grouped action shells and multi-column control stability
- Status: `PASS`
- Source: tester verification against `Game_Design.md` sections `8` and `8A`
- Priority: `P1`
- Coder Target:
  - `gridline/app.py`
  - `tests/test_simulation.py`
- Bug Description: The new grouped action shells stay mounted and the multi-column labels remain readable, but the entire action region still moves vertically when the selection/details block changes height. That violates the approved requirement that action groups keep consistent positions and footprints so the sidebar appears stationary through normal selection changes.
- Reproduction Steps:
  1. Launch the current build at the default minimum supported `1280x720` window.
  2. Select an empty hardpoint and note the `Actions` section positions.
  3. Select a hardpoint with a built tower such as a `Seed Tower`, then compare the action-group positions again.
  4. Repeat with another occupied hardpoint type to confirm the shift is tied to detail-block growth rather than a one-off group layout issue.
- Expected vs. Actual Result:
  - Expected: The grouped action shells keep consistent vertical positions and footprints while only their active emphasis or internal contents change.
- Actual: Re-test confirmed the fix. Direct runtime probes at `1280x720` kept the grouped action-shell positions unchanged across empty, `Seed Tower`, and `Basic Tower` selections, while the directional clean/harvest impact cues remained distinct.
- QA Verification Notes:
  - Targeted direct-test execution passed the focused regressions covering stationary action-group positions, grouped layout behavior, empty-hardpoint scroll reset, and distinct clean-vs-harvest impact typing.
  - The runtime position probe held exactly at `build_y=0`, `tower_y=92`, `seed_y=355`, and `power_y=561` across empty, `Seed Tower`, and `Basic Tower` selection states at `1280x720`.
  - A wide-value-range probe kept the shortened build label readable under affordability changes (`Basic | 55c | Need 55c` -> `Basic | 55c`) without introducing new shell movement.

### BUG-019: Secondary-mode tradeoffs and power-tower timing still do not read as strong late-use decisions
- Feature Tested: Section 20 role separation, secondary-mode usefulness, and power-tower timing/value
- Status: `PASS`
- Source: tester live-config evaluation against `game_summary.md` current milestone and `Game_Design.md` section `20`
- Priority: `P1`
- Coder Target:
  - `gridline/simulation.py`
  - `gridline/spec.py`
  - `game_config.json`
  - `tests/test_simulation.py`
- Bug Description: Earlier retunes kept the immediate full-charge opener exploit blocked and preserved the minute-two floor, but late-use power value still lagged: competent mixed and power-leaning follow-ups stopped short of a real charge/deploy decision, so the power tower did not yet read as a convincing emergency-stabilizer timing choice in this lane.
- Reproduction Steps:
  1. Run the current live-config guard checks by directly invoking `test_live_config_opener_styles_reach_the_minute_two_checkpoint_window()`, `test_live_config_power_rush_can_reach_a_real_power_deploy_window()`, and `test_live_config_starting_economy_cannot_buy_full_power_charge_immediately()` from `tests/test_simulation.py`.
  2. Run paired seeded simulations on seeds `1`, `7`, and `13` with identical build orders except for one change: leave a tower in default mode versus buying and activating its fixed secondary mode (`Basic` vs `Guard`, `Seed` vs `Recall`, `Burst` vs `Focus`).
  3. Run a mixed three-tower line that keeps expanding normally, then rerun the same line while diverting post-stabilization income into power funding.
  4. Run the current power-leaning follow-up on seeds `1`, `7`, and `13` and record `highest_power_funding`, `charge_stored`, and `power_deploy_count`.
  5. Compare `run_duration`, corruption pressure, and practical power usage to see whether the stronger live config now makes later funding and secondary swaps feel worthwhile rather than merely non-fatal.
- Expected vs. Actual Result:
  - Expected: Secondary modes should solve real situational weaknesses without replacing default behavior in ordinary play, and power funding should create a meaningful clutch timing/value decision rather than either crowding out expansion or reading as ignorable.
  - Actual: Re-test confirmed the late-use fix. `python -m pytest tests/test_simulation.py -q -k "game_config_overrides_runtime_spec or minute_two_checkpoint_window or power_rush_can_reach_a_real_power_deploy_window or starting_economy_cannot_buy_full_power_charge_immediately or mixed_follow_up_reaches_a_broader_late_funding_window or delayed_power_follow_up_holds_the_late_funding_floor"` returned `6 passed`; direct seeded helper probes reproduced `100%` funding plus real deploys in both the mixed and delayed follow-ups across seeds `1` / `7` / `13`; and the direct power-rush line still topped out at `70%` funding with `0` deploys across those same seeds instead of becoming the new dominant rush.
- QA Verification Notes:
  - The deferred app-layer smoke also held: an instrumented `GridlineApp` probe reported `tick_ms=16`, `sidebar_refresh_interval=0.1`, `render_calls=120`, `refresh_calls=19`, `active_orbs=3`, and `game_over=False` across `120` live loops.
  - Stronger seeded late-game lines can recycle power repeatedly once stabilized, so repeated redeploy volume should stay under watch during broader Section 20 evaluation even though the immediate `BUG-019` gate now passes.

### BUG-020: Grid framing overruns the intended playable boundary on the right edge
- Feature Tested: Playfield framing and board-boundary presentation
- Status: `PASS`
- Source: planner triage of `Play_Tester_Notes.md`
- Priority: `P3`
- Coder Target:
  - `gridline/app.py`
  - `gridline/topology.py`
- Bug Description: A playtester reports that the rendered grid continues beyond the apparent row/column boundary of the playable field on the right side. Even if this comes from scaling or padding logic rather than gameplay state, it makes the board extents read incorrectly and weakens the intended clean technical framing.
- Reproduction Steps:
  1. Launch the current build in the default windowed view.
  2. Inspect the right edge of the grid relative to the outer playable lanes and hardpoint envelope.
  3. Compare the visible right-edge termination to the other board edges.
  4. Repeat in fullscreen if needed to determine whether the issue is tied to scaling.
- Expected vs. Actual Result:
  - Expected: The grid should terminate cleanly at the approved playable-area / hardpoint boundary instead of reading as if it extends into non-playable space.
  - Actual: Re-test confirmed the fix. `python -m pytest tests/test_simulation.py -q -k "occupied_hardpoint_selection_resets_action_scroll_to_tower_controls or selection_region_handles_long_detail_overflow_inside_its_own_scroll_body or action_group_positions_stay_stationary_through_selection_changes or rendered_board_surface_uses_topology_playfield_rect"` passed (`4 passed`), and a direct runtime probe showed the rendered `board_surface` rectangle matching `topology.playfield_rect` exactly at `24,24,888,696` in both the default `1280x720` windowed probe and the fullscreen toggle probe.
- QA Verification Notes:
  - The targeted board-surface regression passed.
  - The direct runtime probe showed the darker outer canvas sitting outside the framed board rectangle instead of extending the playable grid read.
  - This closes the accepted right-edge framing issue for the current MVP scope.

### BUG-021: Core controls are not reliably visible on smaller laptop-sized windows
- Feature Tested: Supported minimum-window action visibility and reachability
- Status: `PASS`
- Source: planner triage of `Play_Tester_Notes.md`
- Priority: `P2`
- Coder Target:
  - `gridline/app.py`
  - `tests/test_simulation.py`
- Bug Description: The grouped/stable sidebar pass improved structure, but a playtester still reports that smaller laptop-sized windows can leave some buttons off-screen or otherwise not immediately visible. The approved behavior is that supported-window play does not rely on a large display to expose core actions.
- Reproduction Steps:
  1. Launch the current build in windowed mode at the minimum supported laptop-sized window, or the smallest real laptop resolution the project intends to support.
  2. Select empty and occupied hardpoints that expose different action groups.
  3. Check whether build, upgrade, mode, and power-related controls remain visible or immediately reachable within the structured action region.
  4. Compare against a larger display to confirm the issue is specific to smaller supported windows rather than a general missing-control bug.
- Expected vs. Actual Result:
  - Expected: At the supported minimum window, core actions should remain visible or immediately reachable without relying on a large monitor.
  - Actual: Re-test confirmed the fix. The same focused pytest run passed (`4 passed`), and a direct `1280x720` runtime probe showed the occupied-selection action region resetting to `yview 0.0`, the first `Tower Controls` row staying inside the visible `208 px` action region (`tower_top = 92`), and long selection text overflowing inside the `106 px` detail canvas instead of stealing the action region footprint.
- QA Verification Notes:
  - New regressions `test_occupied_hardpoint_selection_resets_action_scroll_to_tower_controls()` and `test_selection_region_handles_long_detail_overflow_inside_its_own_scroll_body()` passed alongside grouped-shell stability and board-surface termination.
  - The occupied-selection runtime probe also reset the detail scroll back to the top, keeping the detail overflow isolated from the action region.
  - This closes the supported-window reachability issue at the declared `1280x720` support floor.

### BUG-022: Ready shell can hide the primary Start Run control at startup
- Feature Tested: Ready-shell primary action visibility and start-of-session reachability
- Status: `PASS`
- Source: tester follow-up after live user report against `FEATURE-RAIL-001`
- Priority: `P0`
- Coder Target:
  - `gridline/app.py`
- Bug Description: The ready shell currently tells the player that `Start Run` is the primary action, but at the default `1280x720` startup size the bottom `Utility` section collapses to effectively zero visible height. The `start_run` button remains packed, yet it renders outside the visible sidebar viewport, so the player cannot reliably start the run from the ready shell.
- Reproduction Steps:
  1. Launch the app into the default ready shell.
  2. Leave the window at the default startup size (`1280x720` in the current runtime spec).
  3. Inspect the bottom `Utility` section where `Start Run` should appear.
  4. Compare the visible sidebar content to the ready-shell overlay text that calls out `Start Run` as the primary action.
- Expected vs. Actual Result:
  - Expected: The ready shell shows a visible, reachable `Start Run` button inside the sidebar command rail at startup.
  - Actual: Re-test confirmed the fix. Focused pytest checks passed, and direct runtime probes at the default `1280x720` startup window measured `utility_h=114`, `start_h=23`, and `button_y=667`, leaving the `Start Run` control visible and reachable without resizing.
- QA Verification Notes:
  - `python -m pytest tests/test_simulation.py -q -k "utility_frame_winfo_height or sidebar_uses_contextual_action_groups or shell_flow_boot_pause_resume_and_defeat_replay or power_status_and_actions_show_funding_and_ready_state_clearly or occupied_hardpoint_selection_resets_action_scroll_to_tower_controls or selection_region_handles_long_detail_overflow_inside_its_own_scroll_body"` passed (`5 passed`).
  - Direct startup probes at both the default runtime spec and an explicit `1280x720` spec kept the ready-shell `Start Run` button visible (`visible=1`).
  - Follow-up runtime checks still held for pause/resume shell flow, critical-phase row/banner behavior, and supported-window action reachability.

### BUG-023: Longer-horizon Section 20 lines overrun the target band and turn power into a repeat-deploy loop
- Feature Tested: Section 20 pacing, role separation, and power-tower late-use role
- Status: `WONT_FIX_MVP`
- Source: tester Section 20 evaluation against `Game_Design.md` section `20`
- Priority: `P1`
- Coder Target:
  - `game_config.json`
  - `gridline/spec.py`
  - `gridline/simulation.py`
  - `tests/test_simulation.py`
- Bug Description: The focused late-use guard suite still passes, but longer-horizon competent style probes now overshoot the approved survival band and produce repeat power redeploy loops. In sampled `secondary-first` and `mixed-then-power` lines, seeds `1`, `7`, and `13` stayed alive through the `1080s` warning cap instead of landing mostly in the 10 to 15 minute target band, and the mixed line recycled power so often that the tower read as routine sustain rather than an emergency stabilizer.
- Reproduction Steps:
  1. Run `python -m pytest tests/test_simulation.py -q -k "minute_two_checkpoint_window or power_rush_can_reach_a_real_power_deploy_window or starting_economy_cannot_buy_full_power_charge_immediately or mixed_follow_up_reaches_a_broader_late_funding_window or delayed_power_follow_up_holds_the_late_funding_floor"` to confirm the short-horizon Section 20 guards still pass.
  2. Run seeded live-config simulation probes for `secondary-first` and `mixed-then-power` on seeds `1`, `7`, and `13`.
  3. For `secondary-first`, use a line equivalent to `Basic -> Guard Mode -> Basic fire-rate upgrade -> Seed -> Burst -> Basic`, start funding power around `120s`, and deploy whenever charged.
  4. For `mixed-then-power`, use a line equivalent to `Basic -> Seed -> Burst -> Basic fire-rate upgrade -> Basic -> Recall Mode`, start funding power around `120s`, and deploy whenever charged.
  5. Let each run continue to at least `600s`, then extend representative runs to the `1080s` warning line and record `run_duration`, `highest_power_funding_reached`, and `power_deploy_count`.
- Expected vs. Actual Result:
  - Expected: Most competent losses should land in the 10 to 15 minute band, repeated survival past minute 18 should be exceptional, and the power tower should read as an emergency stabilizer instead of a dominant routine loop.
  - Actual: The focused guard suite still passed (`5 passed`), but seeded long-horizon probes on `secondary-first` and `mixed-then-power` survived to the `1080.02s` cap on every sampled seed instead of losing in-band. The `600s` probes already hit `76-78` deploys in `secondary-first` and `9-78` deploys in `mixed-then-power`, and the `1080s` mixed probe reached `156` deploys on each sampled seed. A control `direct power-rush` probe still topped out at `70%` funding with `0` deploys by `600s`, so the issue is not an immediate rush exploit; it is over-stable mid/late play plus excessive repeat power value once a line is established.
- QA Verification Notes:
  - `OBJ-013` and `OBJ-014` remain blocked on this rebalance result.
  - This evidence comes from deterministic seeded simulation probes rather than a manual UI-only play pass, but it is sufficient to reopen the Section 20 balance lane for coder action.
  - Planner has since deferred this lane from the current MVP critical path because the power tower is a non-core supplemental mechanic; return to it only after design, presentation, and core-mechanics completion are in a stronger state.

## Next QA Sequence
1. Re-run smoke and interaction testing after the next coder pass.
2. Move any coder-claimed fixes from `todo` to `verify_fix`.
3. Re-test each bug against the explicit expected result in this file.
4. When a bug passes, add a formal approval or bug-resolution entry to `agent_log.txt`.

## File Maintenance Rules
- Add new bugs under `Active Bug Queue` first, then create a detailed entry if coder action is needed.
- Keep bug IDs stable even if wording changes.
- Update status here before writing the formal `agent_log.txt` entry so the working queue stays current.
- Do not mark `pass` unless the behavior has been re-tested after the relevant code change.
