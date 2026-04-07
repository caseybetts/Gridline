# Gridline Game Design

## Document Purpose

This file is the primary design outline for `Gridline`.
It is intended to translate planner-approved decisions into coder-usable feature specifications while `game_summary.md` remains the planner-owned product vision and this file carries the implementation-ready gameplay rules.

## Usage Rules

- Add new mechanics here before or alongside implementation.
- Treat each major gameplay system as its own specification section.
- Prefer explicit rules and edge cases over broad intent statements.
- Keep this document state-agnostic. Live priorities, active bugs, and sprint status belong in `CURRENT_HANDOFFS.md`, `QA_TRACKER.md`, or `agent_log.txt`, not here.

## Product Summary

- Genre: grid-based tower defense / corruption containment.
- Platform: PC, windowed by default, fullscreen toggle supported.
- Mode: endless survival.
- Run target: 10 to 15 minutes.
- Core fantasy: clean and contain corruption across a glowing line network under escalating pressure.
- Primary loss condition: corruption exceeds 80 percent of the allowed threshold.

## Core Gameplay Loop

1. Start a run with a partially neutral grid, starting currency, and empty edge hardpoints.
2. Enemies and corruption pressure begin immediately and escalate over time.
3. Spend coins to build towers on empty hardpoints and buy upgrades.
4. Towers automatically fire light-orb projectiles that travel along valid grid lines.
5. Orbs clean corruption, harvest green lines, and help preserve grid integrity.
6. The player balances economy, tower mix, and upgrade timing against corruption spread and enemy pressure.
7. The run ends when corruption passes the failure threshold.

## Design Principles

- The game should read as line-based, not cell-based.
- Player decisions should center on containment, economy, and coverage.
- Randomness should create tactical uncertainty without making outcomes feel arbitrary.
- MVP systems should be modular and testable in isolation.
- Protecting overall grid integrity is the primary survival priority; protecting towers is secondary.
- Base tower archetypes stay distinct even when a tower later gains one secondary behavior or temporary power override.

## Feature Specification Template

### System Name & Goal

- Goal:

### Core Mechanics



### Rules

- 

### Procedures

- 

### Boundaries and Edge Cases

- 

### Outcomes

- 

### Data Requirements

- 

### State Machine / Flow

- States:
- Entry triggers:
- Exit triggers:

### UI / UX Requirements

- 

### Implementation Notes for Coder

- 

### Open Questions

- 

## Feature Specs

### 1. Grid Topology and Rendering

#### System Name & Goal

- Goal: create a dense, readable, multi-tier line field that clearly communicates where all gameplay occurs.

#### Core Mechanics

1. The map is a line network composed of three nested grid tiers: `large`, `medium`, and `small`.
2. All gameplay entities that use the field must anchor to valid line segments or intersections.
3. The playfield scales to fill the available game area while preserving a reserved UI rail.
4. Tier readability is preserved through spacing, brightness, width, and opacity differences.
5. Line visuals update to reflect state changes without changing the underlying topology.

#### Rules

- `large` lines are the base layer and must always remain the easiest tier to read.
- `medium` lines subdivide `large` spaces at half spacing.
- `small` lines subdivide `medium` spaces at half spacing.
- No gameplay entity may appear to travel through cell interiors unless it is explicitly in a launch or landing transition.
- Render priority for static lines is `small` -> `medium` -> `large`.
- Render priority for dynamic effects is line glow -> orb trail -> orb head -> enemies -> HUD.
- Orb trails must remain confined to valid connected grid segments and intersections; they may not cut across cell interiors for visual convenience.
- Orb trails must fade progressively from brightest near the orb head to dimmest at the oldest visible tail segment.

#### Procedures

- On run start, generate the three line tiers from a common playfield rectangle.
- Mark valid intersections for each tier and for cross-tier transitions.
- Recompute visual scale when the window size or fullscreen state changes.
- Rebuild line draw geometry without changing line identity/state when only layout scale changes.

#### Boundaries and Edge Cases

- If scale changes mid-run, existing line state data must persist against the same logical line IDs.
- If the smallest tier becomes visually unreadable at a given window size, reduce stroke intensity before removing the tier.
- If a visual effect would obscure state readability, state color takes priority over decorative glow.

#### Outcomes

- The player should immediately understand that the game is played on lines rather than in cells.
- The map should feel denser and more technical as finer tiers are unlocked and used.

#### Data Requirements

- `playfield_rect`
- `ui_rail_width`
- `grid_scale_multiplier`
- `tier_spacing.large`
- `tier_spacing.medium`
- `tier_spacing.small`
- `tier_visuals` per tier: width, alpha, glow_alpha, brightness
- Stable logical IDs for line segments and intersections

#### State Machine / Flow

- States: `layout_ready`, `scaled`, `rendering`
- Entry triggers: game boot, window resize, fullscreen toggle
- Exit triggers: shutdown or next layout recalculation

#### UI / UX Requirements

- The playfield must visually dominate the screen over the sidebar.
- Large lines should be readable at a glance; medium lines readable on focus; small lines readable during action.
- The visual style should stay dark, technical, and glow-driven rather than cartoonish.
- Tail rendering should make recent orb pathing readable through turns and intersections, not just show current heading.

#### Implementation Notes for Coder

- Keep topology identity separate from pixel layout so rescaling does not reset simulation state.
- Tier line widths should remain differentiated after scale changes.

#### Open Questions

- Final sign-off thresholds for line thickness, brightness, and shadow intensity remain open.

### 2. Tower Hardpoints and Build Flow

#### System Name & Goal

- Goal: give the player clear, constrained placement decisions through edge hardpoints rather than freeform tower placement.

#### Core Mechanics

1. Hardpoints exist at predefined edge locations around the playable field.
2. Each hardpoint begins the run empty and directly buildable.
3. If the player can afford a tower, they may build one directly onto an empty hardpoint.
4. A filled hardpoint hosts one permanent tower archetype at a time.
5. If a tower is destroyed, the hardpoint becomes empty again until rebuilt.

#### Rules

- Towers can only be built on empty hardpoints.
- One hardpoint can hold only one permanent tower at a time.
- A tower cannot be switched to another archetype without first removing or losing the existing tower.
- Hardpoints are intended to emit into the map from the edges, not the interior.

#### Procedures

- Player selects a hardpoint.
- If empty and the player has enough coins, the build menu for available tower archetypes becomes available.
- If occupied, the sidebar shows that tower's shared upgrade paths and status readout.

#### Boundaries and Edge Cases

- If the player cannot afford a tower, the hardpoint remains selectable but build actions are disabled with clear cost feedback.
- If a tower is destroyed during a surge, the hardpoint should remain available for rebuilding after the threat passes.
- If a hardpoint lacks a clean valid emission point for the tower's current access tier, emission snaps to the nearest valid intersection.
- If interior influence from edge hardpoints feels too weak, first correct `Basic Tower` and `Seed Tower` emission/pathing behavior before changing hardpoint count or placement rules.

#### Outcomes

- Placement decisions are readable, deliberate, and fast to execute.
- Losing a tower is a setback, but losing a hardpoint is not intended as a punishment loop for MVP.

#### Data Requirements

- `hardpoint_id`
- `position`
- `edge_side`
- `is_empty`
- `installed_tower_type`
- `tower_hp_current`
- `tower_hp_max`

#### State Machine / Flow

- States: `empty`, `occupied`, `destroyed_waiting_rebuild`
- Entry triggers: run start, tower build, tower destruction
- Exit triggers: build, destruction, rebuild

#### UI / UX Requirements

- Empty hardpoints should be visible and read as available infrastructure.
- Occupied hardpoints should clearly show tower type and current health.
- Invalid actions should provide feedback through disabled buttons or cost warnings, not silent failure.

#### Implementation Notes for Coder

- Hardpoint availability should be independent from tower survival so rebuilding does not require any separate unlock step.

#### Open Questions

- Tower sell/scrap is not part of MVP.
- Hardpoint-count expansion is deferred until post-fix playtesting shows that improved emission/pathing behavior still fails to create meaningful interior coverage.

### 2A. Tower Archetypes and Secondary Behavior Access

#### System Name & Goal

- Goal: preserve strong tower identity through base archetypes while allowing limited per-tower flexibility through one purchasable secondary behavior.

#### Core Mechanics

1. At build time, the player chooses one base tower archetype for the selected empty hardpoint.
2. Each archetype has a default role bias, default orb behavior, and per-tower snake parameters.
3. Each placed tower may purchase exactly one additional orb behavior during the run.
4. The secondary behavior is a meaningful tradeoff against economy, expansion, and raw upgrades.
5. Secondary behavior access adds situational flexibility but does not erase the tower's base role identity.

#### Rules

- MVP includes at least three base tower archetypes: `Basic Tower`, `Seed Tower`, and `Burst Tower`.
- Towers are not universal interchangeable chassis.
- Secondary behavior access is per tower instance, not a global unlock for all towers of that type.
- Each placed tower may buy exactly one secondary behavior, not unlimited behavior accumulation.
- Base archetype role bias must remain legible even after secondary behavior access is unlocked.
- For MVP, each archetype has one fixed secondary behavior option rather than a broad shared shortlist.
- Switching between default and purchased secondary behavior is a manual player action gated by a cooldown.
- `Basic Tower` role bias: balanced all-rounder with the strongest defensive secondary posture.
- `Seed Tower` role bias: strongest long-reach map control and corruption-response tool, weaker local defense by default.
- `Burst Tower` role bias: strongest local area denial and enemy interception, weakest sustained long-range coverage.

#### Procedures

- Player selects one base archetype to build.
- Built tower starts with its archetype-default behavior.
- Later, if the player can afford it, that specific tower may purchase one additional orb behavior option.
- After purchase, the player may manually swap between default and secondary behavior, subject to a cooldown gate.

#### Boundaries and Edge Cases

- If a tower is destroyed, its purchased secondary behavior is lost with that tower instance.
- If a tower is under temporary power tower override, switching between default and purchased secondary behavior is suspended until power mode ends.
- If the player cannot afford the secondary behavior purchase, the tower remains in its default state.

#### Outcomes

- The player gets both strong archetype clarity and limited adaptation on vulnerable or strategically important hardpoints.

#### Data Requirements

- `tower_archetype`
- `default_behavior_profile`
- `secondary_behavior_option`
- `secondary_behavior_cost`
- `behavior_swap_cooldown`
- `snake_tail_length`
- `snake_speed`
- `turn_chance`
- `lifetime`

#### State Machine / Flow

- States: `base_only`, `secondary_available`, `default_active`, `secondary_active`, `swap_cooldown`, `temporarily_overridden_by_power`
- Entry triggers: tower build, unlock visibility, purchase, manual swap, power deploy
- Exit triggers: purchase, swap, cooldown expiry, power expiry, tower destruction

#### UI / UX Requirements

- The selected tower panel must clearly show base archetype and current active behavior.
- Secondary behavior purchase must read as an optional specialization, not as a mandatory upgrade tax.

#### Implementation Notes for Coder

- Model base archetype data separately from temporary or optional behavior overlays.

#### Open Questions

- The starter purchase costs and shared swap-cooldown defaults are defined in Sections `14` and `20`; later tuning may revisit the numbers, but the mechanic is implementation-ready for the current MVP pass.

### 2B. Base Tower Archetypes

#### System Name & Goal

- Goal: define the initial three tower identities that structure player build decisions.

#### Core Mechanics

1. `Basic Tower` emits from the tower location and favors mostly straight, predictable orb travel.
2. `Seed Tower` launches a seed deep into the map; on landing, it releases an orb with more random walk.
3. `Burst Tower` emits multiple orbs from the tower with highly random walk and shorter lifespan.

#### Rules

- `Basic Tower` should provide the most even baseline mix of cleaning, enemy pressure, and reliability.
- `Seed Tower` should be the strongest remote corruption-response archetype and the weakest at immediate point defense.
- `Burst Tower` should be the strongest short-range interception and local panic-control archetype.
- Upgrade paths can shift a tower somewhat toward cleaning or damage, but should not fully collapse archetype identity.
- `snake_tail_length` is per tower/archetype value, not one global value for every tower.
- `shot_range` matters primarily for projectile-launching towers such as `Seed Tower` and power tower behavior as applicable.

#### Procedures

- On build, instantiate the chosen archetype's default parameters.
- Apply archetype-specific firing, movement, and target-selection logic.
- Apply global upgrades for that archetype on top of the base values.

#### Boundaries and Edge Cases

- A tower's purchased secondary behavior may alter movement/output style but should not rewrite its base upgrade track.
- If a hardpoint is near the edge of a legal launch profile, launch points must still snap to valid intersections.

#### Outcomes

- Tower choice at build time creates meaningful role differentiation.

#### Data Requirements

- `build_cost`
- `fire_rate`
- `shot_cost`
- `snake_speed`
- `snake_tail_length`
- `hit_damage`
- `hp`
- `shot_range`
- `default_behavior_profile`

#### State Machine / Flow

- States: `built_basic`, `built_seed`, `built_burst`
- Entry triggers: tower construction
- Exit triggers: tower destruction, temporary power override

#### UI / UX Requirements

- Build choices must communicate role bias before purchase.
- Selected tower details must display archetype name and relevant per-tower parameters.

#### Implementation Notes for Coder

- Keep archetype definitions explicit in data so tuning remains transparent.

#### Open Questions

- The starter archetype profiles are defined in Section `13`; later tuning may adjust them, but the base tower roles and implementation defaults are locked for the current MVP pass.

### 2D. Fixed Secondary Behavior Mapping

#### System Name & Goal

- Goal: define the single allowed secondary behavior option for each MVP tower archetype so flexibility remains bounded and coder implementation stays deterministic.

#### Core Mechanics

1. Each base tower archetype has exactly one planner-approved secondary behavior option in MVP.
2. A placed tower may purchase only its own mapped secondary option.
3. Once purchased, the tower can manually switch between default and secondary behavior using the cooldown-gated swap action.

#### Rules

- `Basic Tower -> Guard Mode`
- `Seed Tower -> Recall Mode`
- `Burst Tower -> Focus Mode`
- No archetype may access another archetype's secondary behavior unless the Planner changes scope later.

#### Procedures

- Build tower.
- Offer only that tower archetype's mapped secondary behavior in the UI.
- On purchase, unlock manual behavior swapping for that tower instance.

#### Boundaries and Edge Cases

- If the tower is in `swap_cooldown`, additional swap attempts fail with clear feedback.
- If the tower is under power-tower override, swapping is disabled until the override ends.

#### Outcomes

- The player gets bounded adaptation without combinatorial design sprawl.
- Each secondary mode should reinforce its host tower's identity rather than overwrite it.

#### Data Requirements

- `tower_archetype`
- `fixed_secondary_behavior_profile`
- `behavior_swap_cooldown`

#### State Machine / Flow

- States: `default_only`, `secondary_unlocked`, `default_active`, `secondary_active`, `swap_cooldown`
- Entry triggers: build, purchase, manual swap
- Exit triggers: purchase, swap, cooldown expiry, destruction

#### UI / UX Requirements

- The purchase panel should show only one secondary option for each tower.
- The selected tower panel should display current active behavior and swap cooldown status.

#### Implementation Notes for Coder

- Keep the mapping explicit in config/data rather than inferred from generic tags.

#### Open Questions

- Purchase costs and starter per-mode values are defined in Section `14`; later tuning may adjust them, but the fixed mapping and current defaults are implementation-ready now.

### 2E. Secondary Behavior Definitions

#### System Name & Goal

- Goal: define the planner-locked secondary behavior for each base tower archetype so the Coder can implement bounded stance-style flexibility.

#### Core Mechanics

1. `Basic Tower` may buy `Guard Mode`.
2. `Seed Tower` may buy `Recall Mode`.
3. `Burst Tower` may buy `Focus Mode`.
4. Each purchased mode is toggled manually and uses the shared swap cooldown system.

#### Rules

- `Guard Mode`: shorter-range, tower-centered defensive behavior that prioritizes local enemy interception and nearby line stabilization over deep cleaning reach.
- `Recall Mode`: replaces deep launch behavior with shorter-range defensive seeding around the hosting hardpoint, creating a local containment posture instead of remote map reach.
- `Focus Mode`: compresses the burst into fewer, more directed shots with better forward reach and cleaner lane pressure, trading away some of the default chaos and close-defense saturation.
- Secondary modes should improve a real situational weakness without removing the need for tower mix and placement planning.

#### Procedures

- On secondary purchase, unlock the mapped mode for that tower instance.
- On player swap input, if not cooldown-locked, switch the tower to the mapped secondary mode.
- On next valid swap input after cooldown, allow return to default mode.

#### Boundaries and Edge Cases

- If a mode switch is attempted during cooldown, reject the swap and provide clear feedback.
- If a power-tower override begins while a secondary mode is active, the secondary state is suspended and should resume only if it was the active pre-power state when the override ends.

#### Outcomes

- The player can reorient a tower between its default identity and a planner-approved fallback posture without opening full stance combinatorics.

#### Data Requirements

- `guard_mode_profile`
- `recall_mode_profile`
- `focus_mode_profile`
- `behavior_swap_cooldown`
- `active_behavior_mode`
- `pre_power_behavior_mode`

#### State Machine / Flow

- States: `default_active`, `guard_mode`, `recall_mode`, `focus_mode`, `swap_cooldown`, `power_override`
- Entry triggers: purchase, manual swap, power deploy
- Exit triggers: swap, cooldown expiry, power expiry, destruction

#### UI / UX Requirements

- The selected tower panel must show the current named mode, not just a generic "secondary active" flag.
- Purchase and swap actions should use the explicit mode names `Guard Mode`, `Recall Mode`, and `Focus Mode`.

#### Implementation Notes for Coder

- Treat each named mode as a data profile override attached to a specific archetype, not as a shared generic mode system across all towers.

#### Open Questions

- Section `14` defines the starter secondary-mode overrides. Treat those as the current implementation defaults and revisit only in later tuning work.

### 2C. Seed Tower Targeting Controls

#### System Name & Goal

- Goal: give the player limited influence over Seed Tower targeting bias without eliminating uncertainty.

#### Core Mechanics

1. `Seed Tower` acquires targets through weighted probabilistic rules rather than fully deterministic targeting.
2. The player adjusts three targeting levers that influence the next target choice.
3. The tower then launches a seed toward the chosen target area and releases its orb behavior on landing.

#### Rules

- `closest_vs_random` default: `70/30`
- `red_vs_green` default: `70/30`
- `darkest_vs_random` default: `60/40`
- These levers bias target choice; they do not guarantee a specific result every shot.
- Each lever is clamped to `0..100` in `5`-point increments.
- Each lever is displayed as a split that sums to `100` at all times.

#### Procedures

- Build or select a Seed Tower.
- Read current lever settings.
- On each target acquisition, build the valid candidate set inside `shot_range`.
- Apply targeting in staged order rather than blended weighting:
  - Stage 1: roll `red_vs_green`; attempt preferred color bucket first, fall back to the other color if empty.
  - Stage 2: inside the surviving bucket, roll `closest_vs_random`; attempt the closest-distance subset first, fall back to full bucket if empty.
  - Stage 3: inside the surviving bucket, roll `darkest_vs_random`; attempt the highest-intensity subset first, fall back to the current bucket if empty.
  - Stage 4: if multiple candidates still remain, choose randomly from the remaining equal candidates.
- Launch seed toward the selected target area.

#### Boundaries and Edge Cases

- If no valid target exists for a preferred category, the tower falls back to the next valid candidate pool rather than idling forever.
- If the target line state changes before the seed lands, the orb resolves against the current live state at landing time.
- If no red or green target exists in range, the tower may target a blue line using the same closest/random logic to avoid fire stalls.
- Lever stages do not multiply weights together in MVP; they are resolved as ordered preference checks.

#### Outcomes

- Seed Tower remains partially controllable without becoming fully deterministic.

#### Data Requirements

- `closest_vs_random`
- `red_vs_green`
- `darkest_vs_random`
- `shot_range`
- `valid_target_filters`
- `target_selection_pipeline`
- `candidate_bucket`

#### State Machine / Flow

- States: `acquiring_target`, `launching_seed`, `seed_in_flight`, `landing_release`
- Entry triggers: fire opportunity, valid target set
- Exit triggers: target acquired, seed launched, landing reached

#### UI / UX Requirements

- Lever values should be visible and adjustable from the selected Seed Tower panel.
- The UI should communicate that values are weighting biases, not hard locks.

#### Implementation Notes for Coder

- Keep targeting weights data-driven and expose them in config.

#### Open Questions

- Lever defaults are locked for MVP; later tuning may revise defaults but not the clamp/display model.

### 3. Orb Firing and Line Travel

#### System Name & Goal

- Goal: define the main player power expression through automated light-orb firing, readable travel, and line cleaning behavior.

#### Core Mechanics

1. Towers fire automatically according to their `fire_rate` if they can pay the `shot_cost`.
2. On firing, an orb is spawned at the tower's emission point or at a valid launch point defined by that tower archetype.
3. Orbs travel only along legal line segments for the tower's current `grid_access_tier`.
4. Orbs choose directions according to archetype-specific path behavior.
5. As an orb moves, it applies cleaning and/or harvesting effects to the line segments it traverses.
6. Orbs expire when they run out of lifetime, range budget, or trail budget.

#### Rules

- Default access begins on `large` lines only.
- Upgrading `grid_access_tier` expands legal travel from `large` -> `medium` -> `small`.
- Orbs may only turn at valid intersections for their current tier.
- Orbs cannot jump between disconnected line positions.
- Firing is skipped, not queued, if a tower cannot afford the shot cost at the moment of fire.
- Orb visibility is part of gameplay readability and not optional polish.
- Line interaction is continuous by distance traveled rather than discrete only at segment boundaries.
- U-turns are not legal during normal travel unless the orb reaches a dead end and no other legal move exists.
- Once a tower unlocks finer tiers, orbs may use them but do not forcibly prefer tier transitions unless their archetype/mode says so.
- Orb tail visuals must be a path-faithful rendering of recent traveled distance along the orb's actual connected segment history, not a straight-line approximation from head to prior position.
- Tail fade must be strongest at the orb head and progressively weaken backward along the path so older traveled segments are visibly fainter.

#### Procedures

- Check tower cooldown.
- Check shot affordability.
- Acquire launch target or launch direction according to tower archetype rules.
- Spawn orb on the nearest legal start point.
- Move orb each update along its current line direction.
- Accumulate traveled distance on the current line segment.
- At intersections, resolve turn/continue behavior using that orb's movement profile.
- Resolve intersection choice using the archetype/mode rules below:
  - `Basic Tower`: prefer continuing straight if legal; otherwise choose randomly among non-reverse exits.
  - `Basic Tower / Guard Mode`: treat `effective_range_cap = 150 px` as the local defense radius. At each intersection, evaluate each legal non-reverse exit by the Euclidean distance from the hosting hardpoint to that exit segment's far endpoint. Prefer exits whose far endpoint is `<= 150 px`; among those choose the one with the smallest absolute difference to `150 px`. If none are inside the radius, choose the exit with the smallest far-endpoint distance to the hosting hardpoint. Break any remaining tie by preferring an enemy-adjacent segment, then preferring a non-red segment, then random choice among the tied exits.
  - `Seed Tower`: choose randomly among non-reverse exits using `turn_chance`, with no forward bias after landing.
  - `Seed Tower / Recall Mode`: treat `launch_range_override = 160 px` as the local defense radius after landing. At each intersection, evaluate each legal non-reverse exit by the Euclidean distance from the hosting hardpoint to that exit segment's far endpoint. Prefer exits whose far endpoint is `<= 160 px`; among those choose the one with the smallest far-endpoint distance to the hosting hardpoint. If none are inside the radius, choose the exit with the smallest far-endpoint distance to the hosting hardpoint anyway. Break any remaining tie randomly.
  - `Burst Tower`: at each intersection, assign each legal non-reverse exit a weight. Start from `1.0`. If the angular deviation from the current heading is `< 30 degrees`, multiply by `0.35`. If the angular deviation is `>= 30 degrees`, multiply by `1.0 + turn_chance`, using the current MVP default `turn_chance = 0.48` for a turn weight of `1.48`. Normalize those weights and make one weighted random selection. This is the full MVP anti-straight bias; do not apply any additional heuristics.
  - `Burst Tower / Focus Mode`: sort legal non-reverse exits by absolute angular deviation from current heading, ascending. Keep only the best two exits from that ordering. If only one exit remains, take it. If two exits remain, choose the most-forward exit with probability `forward_bias = 0.70` and choose the second-most-forward exit with probability `0.30`. Use random tie-break only when two exits have exactly equal angular deviation.
- Apply cleaning or harvest contribution continuously as distance is traveled.
- Remove orb on expiry.

#### Boundaries and Edge Cases

- If no valid launch point exists at the exact hardpoint position, snap to the nearest valid intersection for the current access tier.
- If an orb reaches a dead end, it performs a forced U-turn once and then continues until the next normal decision point or expiry.
- If multiple orbs affect the same line on the same update, their cleaning effects stack additively unless a later system rule overrides that.
- If a line changes color while an orb is currently traversing it, the orb uses the line's current state at the time the cleaning check is applied.
- Distance-based cleaning should not require an orb to finish a full segment before producing visible effect.
- When an orb pass causes a real line-state change such as an intensity drop or color conversion, that change must be shown immediately in the same update rather than delayed behind a later visual refresh.

#### Outcomes

- Players should be able to see that towers are firing without relying on debug tools.
- Different tower archetypes should feel meaningfully different through movement pattern and area coverage.

#### Data Requirements

- `fire_rate`
- `shot_cost`
- `snake_speed`
- `snake_tail_length`
- `hit_damage`
- `shot_range`
- `grid_access_tier`
- `turn_chance`
- `lifetime`
- `launch_mode`
- `allowed_tiers`
- `clean_per_unit_distance`
- `harvest_per_unit_distance`
- `distance_traveled_current_segment`
- `forced_uturn_used`
- `home_hardpoint_id`
- `tail_path_history`
- `tail_fade_profile`

#### State Machine / Flow

- States: `ready`, `cooldown`, `spawned`, `traveling`, `expiring`, `removed`
- Entry triggers: cooldown complete, successful fire, movement update, expiry condition
- Exit triggers: shot fired, cooldown starts, lifetime ends, no valid continuation, collision/impact resolution

#### UI / UX Requirements

- Orb head, trail, and glow must remain readable against all three line tiers.
- The trail must stay visually on-grid through turns, intersections, and segment transitions.
- Tail brightness should clearly decay from head to oldest visible segment rather than rendering as one uniform-brightness ribbon.
- Orb impact on a line must produce an obvious visual response; when a pass meaningfully reduces a line's actual state, the displayed intensity/color should visibly step down immediately.
- Selected tower panels should show whether the tower is ready to fire or waiting on cooldown/resources.
- Shot activity should be reflected in HUD telemetry.
- A sleek, futuristic orb/trail finish remains a required end-state, but current tuning work should prioritize readable travel and readable impact before pure smoothing polish.

#### Implementation Notes for Coder

- Treat orb travel as line-native movement rather than tile stepping.
- Keep archetype path logic data-driven where possible so tower identities can be tuned without structural rewrites.
- Store enough recent path information to render tails along actual traveled segments instead of reconstructing a shortcut line afterward.

#### Open Questions

- Sections `13`, `14`, and `17` define the current behavior coefficients and movement-profile defaults. Later balance work may revise them, but no extra default pass is needed before implementation.

### 3A. Seed Flight Geometry

#### System Name & Goal

- Goal: define exactly what a Seed Tower is aiming at during seed launch so the Coder can implement launch and landing consistently.

#### Core Mechanics

1. A seed targets an intersection, not a freeform region.
2. Candidate targets are valid medium-tier or large-tier intersections within the tower's `shot_range`.
3. `shot_range` is measured as Euclidean distance from the hosting hardpoint emission point to the target intersection.
4. On landing, the seed releases its orb at the snapped target intersection and that orb begins normal line-native travel.

#### Rules

- If a chosen target becomes invalid only because its line state changed during flight, the landing still occurs at that intersection.
- If a chosen target becomes structurally invalid due to an impossible runtime topology change, snap to the nearest valid intersection of the same allowed tier.
- Seeds do not collide with intervening line states during flight; only the landing target matters for MVP.
- Default `Seed Tower` launch targeting must prefer non-perimeter-adjacent candidate intersections when any legal interior candidate exists within `shot_range`.

#### Procedures

- Build candidate intersection list inside range.
- Partition that list into interior-preferred targets and perimeter-adjacent fallback targets.
- Resolve targeting pipeline.
- Use the interior-preferred set when it is non-empty; otherwise fall back to the full valid target list.
- Launch seed toward selected intersection.
- On arrival, snap to exact intersection coordinates and spawn the released orb.

#### Open Questions

- Seed flight visuals may be tuned later, but landing geometry is locked for MVP.

### 3B. Interior Influence From Edge Hardpoints

#### System Name & Goal

- Goal: ensure default `Basic Tower` and default `Seed Tower` output from edge hardpoints creates meaningful interior-grid influence rather than persistently skating along the perimeter.

#### Core Mechanics

1. Edge hardpoints constrain placement, not the intended area of influence.
2. Default `Basic Tower` and default `Seed Tower` use interior-favoring launch and early-travel rules before resuming their normal movement logic.
3. Local-defense secondary modes may stay closer to the hosting hardpoint, but they should still affect nearby interior lines rather than collapsing into one fixed perimeter lane.

#### Rules

- Default `Basic Tower` must prefer a legal non-reverse exit that increases distance from the nearest map edge when choosing its initial heading or first eligible turn from an edge-origin spawn.
- Once a default `Basic Tower` orb has advanced at least one `large`-grid spacing away from the nearest perimeter, it may resume the standard straight-preference rule from Section 3.
- Default `Seed Tower` must prefer interior launch targets over perimeter-adjacent targets whenever at least one valid interior candidate exists within range.
- On landing, default `Seed Tower` output should prefer an initial exit that increases distance from the hosting edge when a legal inward option exists before falling back to its normal random-walk rule.
- Persistent one-direction default firing from `Seed Tower` is a defect, not acceptable variance.
- `Guard Mode` and `Recall Mode` may remain local by design, but neither mode should deterministically lock onto one perimeter lane if multiple legal near-interior routes exist.
- Do not solve weak interior influence by increasing hardpoint count until these behavior rules have been implemented and re-tested.

#### Procedures

- Determine the nearest originating edge for the spawning or landing tower output.
- Partition legal exits or valid launch targets into `interior_preferred` and fallback groups using distance from the nearest perimeter.
- Use the `interior_preferred` group when non-empty.
- After the orb has crossed the `interior_bias_distance`, resume the archetype's normal movement rules unless the active mode explicitly stays local.

#### Boundaries and Edge Cases

- If a hardpoint geometry offers no legal inward exit at spawn, snap to the nearest legal launch point first and then apply the first later decision that offers inward travel.
- If all valid seed targets are perimeter-adjacent, launching to a perimeter-adjacent target is allowed as the fallback case.
- Interior bias should not create illegal U-turns or ignore cooldown or range rules.

#### Outcomes

- Edge hardpoints should still create meaningful placement strategy while default `Basic Tower` and `Seed Tower` output reaches lines that matter in the interior network.
- Players should be able to see why an edge hardpoint can influence the center of the map instead of only cleaning along the wall.

#### Data Requirements

- `nearest_origin_edge`
- `perimeter_adjacency_threshold`
- `interior_bias_distance = 1 large-grid spacing`
- `prefer_non_perimeter_seed_targets = true`
- `initial_interior_exit_preference = true`

#### State Machine / Flow

- States: `edge_spawned`, `interior_bias_active`, `normal_travel`
- Entry triggers: default `Basic Tower` spawn, default `Seed Tower` launch selection, default `Seed Tower` landing
- Exit triggers: `interior_bias_distance` reached, no inward option exists, orb expires

#### UI / UX Requirements

- Default `Basic Tower` and `Seed Tower` activity should visibly penetrate toward the interior often enough that the player can read them as containment tools rather than edge-only cleaners.

#### Implementation Notes for Coder

- This is a behavior-priority change, not a request for more hardpoints or a new placement system.
- Keep the interior-bias test data-driven so it can be tuned without restructuring the movement system.

#### Open Questions

- The exact perimeter-distance threshold for counting a node as interior-preferred may be tuned after live play, but the bias itself is required now.

### 4. Corruption and Green Line State System

#### System Name & Goal

- Goal: define the territory-control layer that drives failure pressure, cleaning value, and map-state readability.

#### Core Mechanics

1. Every line segment is always in exactly one color state: `blue`, `green`, or `red`.
2. `green` and `red` lines each use the same three intensity levels that represent maturity or severity.
3. Red spread increases loss pressure and pushes the run toward failure.
4. Green spread creates harvest opportunities and economic value.
5. Orb traversal can reduce intensity or clear the line depending on the current state.
6. Spread executes in explicit tier-aware passes across `large`, `medium`, and `small` layers.

#### Rules

- `blue` is neutral and produces no direct benefit or penalty.
- `green` is harvestable and converts to `blue` when harvested.
- `red` is corruption and converts to `blue` when fully cleaned.
- Intensity levels are `1`, `2`, and `3` for both `green` and `red`.
- Both `green` and `red` intensity visuals must map from lighter/less severe at level `1` to darker/denser at level `3`.
- Redder lines require more orb passes or more total cleaning value to clear.
- If `red` and `green` attempt to spread into the same target line during the same resolution step, the target keeps its existing color.
- Loss is triggered when total corruption exceeds the global failure threshold.
- Corruption percent is based on intensity-weighted red occupancy across all line segments.
- Large, medium, and small segments contribute by actual segment length, not equal flat counts.
- Any supplemental impact or harvest cue must be triggered only by a real underlying line-state change or real income award.
- Orb-driven corruption reduction must read as a causal chain in live play: orb contact, affected segment response, and resulting state step must be visually attributable to the same event window.

#### Procedures

- On each spread interval, resolve tier passes in configured order.
- For each spreading source line, evaluate eligible neighboring target lines.
- Apply spread chance and intensity growth according to the line's state and tier profile.
- Resolve simultaneous spread conflicts before committing new states.
- Store persistent fractional clean and harvest progress on each line segment.
- Apply orb travel contributions to those persistent values during the movement phase.
- Apply enemy/spread state changes after orb contributions for the current tick are accumulated.
- Update total corruption percentage after all spread and cleaning events in the interval are resolved using:
`corruption_percent = 100 * sum(red_segment_length * red_intensity_level) / sum(all_segment_length * max_red_intensity_level)`
where `max_red_intensity_level = 3`, only red segments contribute to the numerator, all segments contribute to the denominator, and the final value is clamped to `0..100`.
- When orb interaction causes a real corruption step-down, update the impacted segment cue in the same readable moment as the line-state change rather than delaying the explanation to a later HUD-only update.

#### Boundaries and Edge Cases

- A line cannot be both `green` and `red`.
- Intensity cannot rise above the configured max for that state.
- Cleaning a partially intensified `red` line reduces intensity before color conversion.
- Harvesting a partially intensified `green` line reduces intensity before color conversion.
- If the failure threshold is crossed mid-update, the run ends after the current simulation step resolves.
- Fractional clean/harvest progress persists on a line while it remains in the same color/intensity state.
- When a line changes color or intensity tier, incompatible stored progress resets to zero for the new state.

#### Outcomes

- The player reads the map as a living battlefield of expanding danger and harvest opportunity.
- The corruption meter functions as the primary win-survival pressure.

#### Data Requirements

- `line_state`
- `line_intensity`
- `spread_interval`
- `spread_chance_by_tier`
- `intensity_growth_rules`
- `clean_value_per_orb`
- `harvest_value_per_intensity`
- `corruption_failure_threshold`
- `intensity_levels = 3`
- `line_clean_progress`
- `line_harvest_progress`
- `segment_length_weight`
- `line_state_change_feedback_profile`
- `harvest_result_feedback_profile`

#### State Machine / Flow

- States: `blue`, `green_level_n`, `red_level_n`
- Entry triggers: initialization, spread, enemy effect, orb interaction
- Exit triggers: cleaning, harvesting, spread conversion, loss check

#### UI / UX Requirements

- Blue, green, and red must be readable instantly and never be confused with decorative effects.
- Higher intensity red must look meaningfully darker and more severe than low intensity red.
- Higher intensity green must also step visibly from lighter to darker/denser so players can judge harvest value at a glance.
- Green should read as a positive but temporary opportunity, not a safe permanent state.
- Whenever orb interaction reduces a line's real state by one level or converts it to blue, the visible line treatment should immediately drop by one displayed intensity/color step in that same moment.
- The HUD must show current corruption percentage and failure threshold context.
- If line stepping alone still reads too subtly in live play, a short-lived local impact cue on the affected line segment is required.
- When a green line converts to blue and awards income, show a brief local harvest-result cue such as a floating `+coins` value or equivalent near the orb or affected segment.
- When a red line drops by one visible step or converts fully to blue, show a short-lived local impact cue that clearly reads as corruption being reduced rather than as a generic hit flash.
- The corruption-reduction cue should reinforce direction of change by making the affected segment visibly calmer or cleaner immediately after the orb-caused event, not just brighter for spectacle.

#### Implementation Notes for Coder

- Resolve spread conflicts centrally instead of line-by-line mutation to avoid order bias.
- Keep state color and intensity separate so visuals and mechanics can scale independently.

#### Open Questions

- Intensity thresholds and exact visual treatment per level remain open.

### 5. Economy and Global Upgrades

#### System Name & Goal

- Goal: create the strategic layer where the player chooses between expansion, upkeep by firing, and long-term scaling.

#### Core Mechanics

1. The player starts each run with a fixed amount of coins.
2. Coins are spent on tower construction and global upgrades for each tower archetype.
3. Towers consume coins only when they fire.
4. Coins are earned by harvesting green lines.
5. Upgrades affect all current and future towers of the selected archetype for the current run.

#### Rules

- Enemy kills do not generate income.
- Shot costs are paid per successful shot only.
- Upgrade purchases are permanent for that run and cannot be refunded in MVP.
- Upgrade buttons must show current value and next value before purchase.
- Economy tuning should support early experimentation before becoming restrictive.
- Harvest payout amount is determined by the harvested green line's current intensity, not by a hidden per-archetype coin multiplier.
- Tower archetypes differ economically through path coverage, `harvest_per_unit_distance`, fire cadence, and shot-cost pressure rather than through separate bonus coin values unless the Planner later changes scope.
- There is no dedicated harvest-income upgrade track in the current MVP; economy improvements come indirectly through the approved existing stat and behavior systems.

#### Procedures

- Award harvest income when a green line is converted to blue.
- Deduct build/upgrade costs immediately on successful purchase.
- Deduct shot cost immediately when a shot is created.
- Block purchases that the player cannot currently afford.

#### Boundaries and Edge Cases

- If the player has enough money to build but not enough to sustain firing, the tower still builds and may idle when broke.
- If multiple towers fire on the same frame, each shot resolves affordability independently.
- If a global upgrade is purchased while orbs are already in flight, the upgrade affects only future shots unless explicitly defined otherwise later.

#### Outcomes

- Players should constantly choose between immediate board presence and longer-term efficiency.
- Green territory should matter because it is the only recurring income stream.

#### Data Requirements

- `starting_coins`
- `build_cost_by_tower`
- `upgrade_cost_by_tower_and_stat`
- `current_upgrade_level_by_tower_and_stat`
- `harvest_income_by_green_intensity`
- `shot_cost_by_tower`
- `recent_harvest_income`
- `selected_tower_economy_snapshot`

#### State Machine / Flow

- States: `solvent`, `constrained`, `broke`
- Entry triggers: start run, spend coins, harvest income
- Exit triggers: income gain, purchase, shot cost payment

#### UI / UX Requirements

- Current coin total must always be visible.
- Disabled actions must clearly indicate insufficient funds.
- Upgrade panels must communicate archetype-wide impact.
- During active tuning, the HUD or selected-object panel must make recent harvest gains attributable enough that testers can tell what income was just earned and which tower behavior produced it.
- During active tuning, selected tower details should expose `shot_cost` plus harvest-relevant output values or clear qualitative equivalents so testers can compare economy behavior across archetypes and modes.

#### Implementation Notes for Coder

- Global upgrades should be stored per tower archetype, not per tower instance.
- If tester clarity still suffers, temporary telemetry is allowed for recent harvest gains and selected-tower economy contribution as long as it does not invent new permanent economy mechanics.

#### Open Questions

- The starter economy and upgrade defaults in Sections `12` through `14` are sufficient for the current MVP pass. Cost curves and scaling formulas can be revisited later during explicitly reopened tuning work.

### 6. Enemy Pressure and Surge Events

#### System Name & Goal

- Goal: provide escalating pressure that attacks both the player's infrastructure and overall grid integrity.

#### Core Mechanics

1. Enemies spawn continuously with randomized timing.
2. Overall pressure increases by level over time, primarily through spawn count and spawn rate scaling.
3. Enemies travel only on valid grid lines and intersections.
4. Enemies threaten the player directly by damaging towers and indirectly by creating or accelerating corruption.
5. Random surge events temporarily intensify corruption-focused pressure.
6. MVP enemy design begins with two enemy archetypes: a corruption seeder and a tower striker.

#### Rules

- Endless survival is the only required mode for MVP.
- Bosses are excluded from MVP.
- Corrupter-focused surges are the priority event type for MVP.
- Enemies must respect line topology the same way orbs do, even if their movement rules differ.
- Enemy pressure scaling should be felt gradually during baseline play and sharply during surges.
- `Corruption Seeder`: travels a random path through the grid, then stops and converts its end line into a red corruption source.
- `Tower Striker`: travels a semi-random path that ultimately resolves toward a tower target and deals tower damage on arrival unless destroyed first.
- Corruption-capable enemies must telegraph impending corruption with a readable light-red to darker-red progression before the corruption event resolves.
- When a corruption-capable enemy actually seeds corruption, it may emit a brief pulse or burst effect at the release moment so players can immediately identify the event.
- If no valid tower target exists, `Tower Striker` falls back to a corruption-pressure role by pathing to a valid interior line target and creating a red corruption source on arrival.
- Fallback targeting priority is deterministic and resolved in ordered steps: non-red interior lines first, then closer-to-center targets, then higher-connectivity targets, then green over blue, then random among remaining ties.
- `Tower Striker` uses a precomputed shortest-path route to its current target, with occasional rerolls at intersections according to its path-turn-chance when an alternate branch still reduces remaining path distance.
- `Corruption Seeder` uses local step-to-step pathing with anti-backtracking: it avoids immediate reversal unless trapped.

#### Procedures

- Spawn enemies using the current level's spawn rules.
- Move enemies along legal paths.
- Resolve `Corruption Seeder` path completion by spawning a red line state at its end location.
- Resolve `Tower Striker` pathing by selecting a tower target, computing a shortest route, and allowing limited branch noise only when the branch still converges.
- If no tower target is valid, reroute `Tower Striker` to an interior line target and resolve it as a corruption-source spawn on arrival.
- Evaluate fallback targets in this ordered priority sequence: non-red first, center-proximate second, high-connectivity third, green over blue fourth, random tie-break last.
- Resolve enemy attacks against towers or grid state according to enemy type.
- Periodically roll for surge activation using configured cadence rules.
- Apply surge modifiers for the surge duration, then return to baseline pacing.

#### Boundaries and Edge Cases

- If a tower is destroyed, its hardpoint remains active and empty.
- If a surge starts while another surge is active, the new surge is ignored unless stacking is explicitly enabled later.
- If enemy corruption effects and natural spread affect the same line in the same interval, both contribute before conflict resolution.
- If no tower exists when a `Tower Striker` needs a target, it must not stall; it immediately switches to its corruption-pressure fallback role.
- `Corruption Seeder` should not bounce back and forth between two segments unless no other legal move exists.

#### Outcomes

- Pressure should come from both board attrition and territory loss.
- Surges should create memorable spikes without replacing the baseline survival loop.

#### Data Requirements

- `spawn_rate`
- `spawn_count`
- `spawn_growth_per_level`
- `enemy_hp`
- `enemy_speed`
- `enemy_contact_damage`
- `corruption_drop_value`
- `surge_cadence`
- `surge_duration`
- `surge_modifiers`
- `enemy_type`
- `targeting_mode`
- `path_randomness`
- `terminal_effect`
- `path_route_cache`
- `anti_backtrack`

#### State Machine / Flow

- States: `baseline`, `escalating`, `surge_active`
- Entry triggers: timer progression, level progression, random surge roll
- Exit triggers: level increase, surge end, game over

#### UI / UX Requirements

- The player should be able to tell when a surge is active.
- Enemy presence should be readable without hiding line-state information.
- A player should be able to tell when a corruption-capable enemy is close to seeding corruption before the seed event actually happens.
- The corruption-seed release moment should read as a discrete event through a short pulse/burst rather than only through the resulting line-state change.

#### Implementation Notes for Coder

- Keep enemy pathing line-constrained from the start to avoid a later rewrite away from cell logic.

#### Open Questions

- Exact connectivity-count implementation details may vary by graph representation, but MVP target selection must follow the ordered priority rules above rather than any weighted scoring system.

### 6A. Escalation Landmarks and Phase Signaling

#### System Name & Goal

- Goal: make endless survival read as an intentional sequence of early, mid, and late pressure phases so players and testers can tell where a run is succeeding or collapsing without relying only on raw survival time.

#### Core Mechanics

1. The run uses named escalation landmarks that sit above moment-to-moment spawn rolls and surge events.
2. Landmark transitions are driven by existing approved pressure signals rather than by adding new enemy classes, new progression systems, or designer-only judgment at runtime.
3. Each landmark transition updates both pacing parameters and player-facing presentation.
4. Surges remain short pressure spikes inside the current landmark; they do not replace the larger run-phase identity.
5. The current phase is always visible in the run-status stack and updates immediately when a transition occurs.

#### Rules

- MVP escalation landmarks are `Opening Containment`, `Escalation`, and `Critical Load`.
- `Opening Containment` begins at run start and covers the opener-economy window where the player is establishing the first tower network and trying to reach the minute-two checkpoint.
- `Escalation` begins once the opener gate is cleared or clearly missed and should represent the main role-separation and build-vs-mode-vs-funding decision window.
- `Critical Load` begins once pressure is high enough that surge recovery, corruption management, and power-tower timing are expected live decisions. This landmark is about pressure state, not about whether the player already owns a stored charge.
- Phase promotion is one-way only: `Opening Containment -> Escalation -> Critical Load`. The run never demotes to an earlier phase.
- The first implementation pass must use the existing live metrics already approved elsewhere in the spec: `level`, `corruption_percent`, and `surge_active`.
- `Opening Containment -> Escalation` occurs on the first update where either `level >= 4` or `corruption_percent >= 20`.
- `Escalation -> Critical Load` occurs on the first update where either `level >= 9`, `corruption_percent >= 45`, or both `surge_active = true` and `corruption_percent >= 35`.
- If the run jumps directly from `Opening Containment` to `Critical Load` because the critical trigger is met first, apply only the `Critical Load` transition feedback. Do not stack two banners back to back.
- Each landmark transition must produce one short readable announcement in both the board-facing presentation and the command rail so the player can feel the phase shift instead of inferring it from hidden numbers.
- Landmark labels should stay active after the transition; they are persistent run-state context, not one-off toast messages.
- If the run extends beyond the intended target band, `Critical Load` persists and intensifies through existing pacing levers rather than inventing a fourth unapproved phase.
- `highest_phase_reached` must update monotonically with the active phase and must never be cleared until a fresh run starts.

#### Procedures

1. Initialize `active_phase = Opening Containment` and `highest_phase_reached = Opening Containment` at the start of every fresh run.
2. Evaluate the phase rules after the simulation update that changes `level`, `corruption_percent`, or `surge_active`, but before the next HUD refresh/render pass completes.
3. Check the `Critical Load` trigger first, then the `Escalation` trigger, so a single sharp spike can promote the run directly to the correct highest phase.
4. When a promotion occurs, update both `active_phase` and `highest_phase_reached` in the same step.
5. Expose the new `active_phase` immediately in the command rail's persistent `Phase` row.
6. Emit one board-facing transition banner for `1.2 s` anchored near the top-center of the playfield using the same typography family as the command rail.
7. During that same `1.2 s` window, pulse the command-rail `Phase` row into its emphasized treatment instead of adding a second long-lived message block.
8. On defeat, freeze the final `active_phase` and report `highest_phase_reached` in the defeat summary even if the loss occurs on the same update as a promotion.

#### Boundaries and Edge Cases

- If the player pauses or resizes during a transition window, the run must not lose or double-fire the landmark transition.
- If corruption spikes sharply enough to jump a run into `Critical Load`, the UI must present one readable `Critical Load` transition rather than silently skipping feedback or replaying both missing phases.
- If a run dies very early, the defeat shell should still report the highest landmark reached even if that is only `Opening Containment`.
- Surges may overlap with landmark transitions, but the player must still be able to tell the difference between `phase changed` and `surge active`.
- If pause opens while a phase-change banner is active, keep the persistent `Phase` row updated immediately; the transient banner may remain frozen and continue for its remaining time after resume, but it must not restart from full duration.
- If defeat resolves while a phase-change banner is active, the defeat summary takes visual priority; do not try to render the lingering banner on top of the defeat shell.

#### Outcomes

- Endless runs feel authored instead of formless.
- Testers can report whether a failure happened in the opener, the main build-vs-power decision window, or the late crisis instead of describing everything as generic balance drift.
- Later balance work has clearer target windows because the product already communicates where the player is in the run arc.

#### Data Requirements

- `phase_id`
- `phase_label = Opening Containment, Escalation, Critical Load`
- `phase_transition_rules = opening_to_escalation(level >= 4 or corruption >= 20), escalation_to_critical(level >= 9 or corruption >= 45 or surge+corruption >= 35)`
- `phase_transition_banner_duration = 1.2 s`
- `phase_status_badge = OPENING, ESCALATION, CRITICAL`
- `phase_pressure_profile`
- `highest_phase_reached`
- `phase_transition_feedback_profile = top-center board banner + command-rail phase-row pulse`

#### State Machine / Flow

- States: `opening_containment`, `escalation`, `critical_load`
- Entry triggers: run start, threshold crossed
- Exit triggers: next landmark reached, defeat

#### UI / UX Requirements

- The active phase must remain visible in the run-status stack as a dedicated persistent `Phase` row without pushing out core survival information.
- Phase-change feedback should be noticeable, brief, and consistent with the command-console visual language rather than a disconnected arcade-style splash.
- Surge alerts and phase labels must be visually distinguishable from one another at a glance.
- Board-facing phase feedback for the first pass should be one slim top-center banner carrying the phase label plus a short descriptor:
  - `Opening Containment`: `Establish the first defense line`
  - `Escalation`: `Multi-front pressure rising`
  - `Critical Load`: `Crisis management active`
- The command rail must show one persistent `Phase` row using the compact badge plus full label, for example `Phase: OPENING | Opening Containment`.
- During a transition pulse, emphasize only the `Phase` row and the board banner; do not shove other status rows downward or open a separate modal.
- The defeat summary should report `highest_phase_reached`, not only the final instant phase, so playtest notes can anchor the run arc immediately.

#### Implementation Notes for Coder

- Keep phase rules data-driven and separate from the one-off visual treatment so tuning can change thresholds without rewriting the shell or HUD.
- Use landmark logic to make pacing legible, not to hide balance problems behind presentation-only dressing.

#### Open Questions

- Later tuning may revise the exact thresholds, but the first implementation pass should use the concrete rules above rather than inventing a different transition mix.

### 6B. Board Event Feedback Layer

#### System Name & Goal

- Goal: define one bounded board-side event-feedback layer so surge state and orb-caused corruption reduction read clearly on the playfield without being confused with phase transitions, harvest popups, or generic hit flashes.

#### Core Mechanics

1. The board uses a transient event-feedback layer above the static line state and below shell/HUD overlays.
2. Surge feedback has two parts: a short activation stinger when a surge begins and a quieter persistent board-edge warning treatment while the surge remains active.
3. Orb-caused red-line reduction uses a local segment-anchored clean/calm cue that appears only when a real red intensity drop or red-to-blue conversion occurs.
4. Surge-active feedback and local corruption-reduction feedback may overlap in time, but they must remain visually distinct through scale, placement, and color language.
5. Phase-change feedback remains a named top-center banner; surge feedback is a threat-state treatment and must not reuse the same presentation shape.

#### Rules

- Surge feedback is board-wide or perimeter-oriented; corruption-reduction feedback is local to the affected segment.
- Surge activation must read as warning/escalation, using the approved warning family rather than the cleaner blue/teal reduction family.
- While `surge_active = true`, the board should carry a persistent but low-duty warning treatment such as perimeter brackets, edge pulse, or corner rails; do not use a second full-width banner that competes with the phase banner.
- Surge-start emphasis should happen once per surge start for a short burst, then settle into the quieter persistent state until the surge ends.
- Orb-caused red-line reduction must read as a calming/cleaning event, not as a damage hit. Prefer a cool-toned sweep, soft collapse, or short-lived afterglow aligned to the affected segment over a bright warm flash.
- The local reduction cue triggers only on real red-state improvement: `red 3 -> red 2`, `red 2 -> red 1`, or `red 1 -> blue`. No cue is emitted for no-op contact, blue-line travel, or green harvest events.
- Green harvest keeps its own local `+coins` event language and must not be recolored to look like corruption reduction.
- If both a phase-change banner and a surge start occur close together, the phase banner keeps the top-center slot and the surge start uses the perimeter/event layer instead of stacking another banner in the same lane.
- If multiple adjacent red segments improve in the same update, each segment may emit its own local cue, but the effect should cap intensity and avoid turning the whole board into a white-noise flash.
- Event feedback must stay readable at the minimum supported `1280 x 720` window and must not depend on inspecting the sidebar first.

#### Procedures

1. On surge start, create one short surge-start event using the board event layer.
2. While `surge_active = true`, render the persistent surge treatment each frame using a low-duty pulse cycle anchored to the board perimeter or corners.
3. On surge end, fade the persistent surge treatment out quickly rather than hard-cutting it off.
4. When orb interaction commits a real red-state improvement, enqueue one local reduction event containing the affected segment, improvement magnitude, and expiration timing.
5. Render local reduction events aligned to the segment geometry after the line-state update is visible, so the player sees `orb contact -> calmer segment -> state result` in one causal window.
6. Remove expired local reduction and surge-start events automatically without changing underlying simulation state.

#### Boundaries and Edge Cases

- If a surge starts while a phase-transition banner is already active, keep the phase banner untouched and use only the surge event layer for the surge start.
- If a surge ends during pause, the persistent warning treatment should remain frozen and then resolve correctly after resume; it must not restart from full intensity.
- If a red segment is improved several times in rapid succession, refresh or stack the local reduction event only up to a capped brightness/width budget; do not let repeated hits create a blinding bar.
- If a red segment improves at the outer edge of the board, the local reduction cue may bleed slightly past the segment for readability, but it must still read as originating from that segment rather than from the whole border.
- If a harvest event and a red reduction event happen near each other, the harvest popup remains text/value-led while the red reduction cue remains a non-text cool clean/calm sweep.

#### Outcomes

- Players can tell the difference between `phase changed`, `surge active`, `surge just started`, and `this orb just calmed corruption here` without reading a text explanation first.
- Board-side feedback feels authored and directional instead of relying on one generic flash language for every event.

#### Data Requirements

- `board_event_feedback_layer`
- `surge_start_event_duration = 0.65 s`
- `surge_persistent_pulse_cycle = 1.10 s`
- `surge_end_fade_duration = 0.25 s`
- `surge_feedback_anchor = board perimeter / corners`
- `surge_feedback_profile = short activation stinger + persistent low-duty perimeter warning`
- `corruption_reduction_event_duration = 0.30 s`
- `corruption_reduction_afterglow_duration = 0.40 s`
- `corruption_reduction_trigger = real red intensity drop or red-to-blue conversion only`
- `corruption_reduction_feedback_profile = segment-aligned cool sweep + short calm afterglow`
- `event_feedback_render_order = line state -> local board events -> orb trails / heads -> enemies -> phase banner / shell overlays`

#### State Machine / Flow

- States: `idle`, `surge_start_event`, `surge_persistent`, `surge_end_fade`, `local_reduction_event`
- Entry triggers: surge start, surge active, surge end, real red-state improvement
- Exit triggers: event duration elapsed, surge resolved, run paused/resumed, game over

#### UI / UX Requirements

- Surge-active feedback must be unmistakable at a glance but quieter than the one-time phase-transition banner.
- The surge warning treatment should frame the board as under pressure rather than obscuring line readability in the center of the field.
- Local corruption-reduction cues should feel cleaner and calmer immediately after orb contact, reinforcing relief rather than impact damage.
- The board event layer should use the same technical visual language as the rest of the game: slim geometry, glow-driven accents, and purposeful motion instead of chunky arcade splashes.
- Board-side event feedback must remain legible when the sidebar is ignored for a few seconds; the player should still understand the current danger and relief events from the playfield alone.

#### Implementation Notes for Coder

- Keep this as a presentation/event-layer pass in `gridline/app.py` or equivalent render surfaces; do not add new gameplay rules or new simulation mechanics.
- Prefer lightweight event records keyed by segment or surge state over ad hoc one-frame flashes.
- Reuse existing topology geometry so local reduction cues follow real segment orientation instead of using generic radial explosions.

#### Open Questions

- No open question for the current MVP pass: use perimeter-oriented surge warning and segment-aligned cool reduction cues as the implementation target.

### 7. Power Tower Event System

#### System Name & Goal

- Goal: add an earned temporary momentum-swing tool without replacing the permanent hardpoint tower game.

#### Core Mechanics

1. The player funds a power tower in 10 percent payment increments.
2. When funding reaches 100 percent, one deployable charge is stored.
3. The player may deploy the charge at a chosen time onto any hardpoint.
4. If deployed onto an empty hardpoint, that hardpoint runs power tower behavior for the active duration.
5. If deployed onto an occupied hardpoint, the existing tower is temporarily overridden by power tower behavior.
6. While active, the power tower provides a short burst of high-impact output.
7. During active time, shots or actions tied to the power tower window are free.
8. After expiration, the hardpoint returns to its prior state and funding can begin again.

#### Rules

- Only one stored power tower charge may exist at a time.
- Partial funding below 100 percent does not grant any active benefit.
- Deployment is manual, not automatic.
- Power tower duration is short and intended as a tactical answer to spikes.
- Power tower is a supplemental mechanic and not a blocker for shell completion, board framing, escalation readability, or core three-tower usability work.
- Power tower is cleaning-first, not pure damage-first.
- Any hardpoint is a valid deployment target, including one that already hosts a permanent tower.
- Deploying onto an occupied hardpoint does not delete the underlying tower; it suspends that tower's normal behavior until power mode expires.
- While suspended, the underlying tower is untargetable and cannot be damaged directly.
- Power tower should immediately operate on the finest-tier traversal intended for MVP.
- Power tower output should be rapid, visually obvious, and free during the active window.
- Power tower should have strong local-to-midfield reach from its hosting hardpoint, not full-map omnipresence.
- Power tower should provide meaningful enemy relief without replacing permanent anti-enemy investment.
- If destroyed early, the player loses the remaining emergency window.

#### Procedures

- Player buys funding chunks until full.
- Stored charge becomes available in the HUD.
- Player selects any hardpoint and deploys the stored charge.
- Save the hardpoint's pre-power state.
- Apply active power tower effects and free-action rules for the configured duration.
- Prioritize high cleaning output while still contributing enough damage to stabilize a collapsing flank.
- Apply incoming damage only to the temporary power tower state while active.
- If power mode expires naturally or the temporary power tower is destroyed early, remove the power state and restore the suspended tower in its pre-power state.

#### Boundaries and Edge Cases

- If the player tries to fund beyond 100 percent, the purchase is blocked.
- If the player already has a stored charge, additional funding is blocked until that charge is used.
- If the run ends while a charge is stored or active, no carryover persists between runs.
- Damage taken during power mode never spills into the suspended underlying tower.

#### Outcomes

- The system creates a controlled panic button and reward loop.
- The core loop must still read as complete if this system remains present but only lightly tuned.

#### Data Requirements

- `funding_increment_percent`
- `funding_cost_per_increment`
- `charge_stored`
- `active_duration`
- `active_range`
- `active_damage`
- `active_clean_value`
- `deployment_target_hardpoint_id`
- `overridden_tower_snapshot`
- `power_is_optional = true`

#### State Machine / Flow

- States: `unfunded`, `partially_funded`, `charged`, `active`, `cooldown_reset`
- Entry triggers: funding purchase, full funding, manual deploy, timer expiry
- Exit triggers: additional funding, deploy, active end

#### UI / UX Requirements

- Funding progress and stored-charge readiness must be visible at all times.
- Active power window must be visually obvious and not mistaken for a standard tower upgrade.

#### Implementation Notes for Coder

- Treat this as a separate temporary system, not as a permanent hardpoint tower archetype.

#### Open Questions

- The starter power-state values in Section `17` are sufficient for the current MVP pass; deeper retuning is deferred and must not block core GUI/mechanics completion.

### 8. HUD, Telemetry, and Player Feedback

#### System Name & Goal

- Goal: ensure the player can understand economy, corruption risk, tower activity, and surge state in real time.

#### Core Mechanics

1. The HUD continuously displays run-critical values.
2. The sidebar is the primary interaction surface for purchases, upgrades, and selected-object details.
3. Temporary telemetry is allowed when it improves tuning and readability.

#### Rules

- The board is the hero surface and the sidebar is the command rail; presentation should reinforce that hierarchy instead of competing with it.
- Corruption percentage must always be visible.
- Coin total must always be visible.
- Active orb count and recent shots fired must be visible during MVP.
- Selected tower readiness or cooldown state must be visible when a tower is selected.
- Surge-active state must be visible when present.
- The right sidebar must be structured into distinct sections rather than one uninterrupted control stack.
- Low-frequency utility actions such as `New Game` must live in a separate utility/menu region, not inside the main tower-control cluster.
- Build controls should appear only when an empty hardpoint is selected.
- Tower-management controls should appear only when a tower is selected.
- Power controls should be visually separated from both tower-build and tower-management controls.
- Harvest-attribution feedback is part of the intended ship-facing readability stack, but it should stay compact: local `+coins` or equivalent near the affected line, one concise `Recent Harvest` status row, and selected-tower recent-income context only while that tower is selected.
- `Esc` toggles the pause shell while a run is active; quitting the application or abandoning the run should happen from the shell, not from the live contextual action stack.
- Fullscreen toggle support is required.
- In the first playable MVP build, active orb count and recent shots fired remain visible by default rather than being hidden behind a debug-only view.
- Selecting an empty hardpoint must reset the contextual action region to the build group immediately so tower-build controls are reachable without blind scrolling.
- If the contextual action region overflows, the first available build actions for an empty hardpoint must still appear inside the visible action region after selection.
- During active tuning, temporary economy-readability telemetry is allowed if needed to show recent harvest gains and the selected tower's harvest-relevant behavior.
- Status text blocks and action groups should remain visually anchored as context changes; avoid layout jump caused by long labels, changing helper text, or inconsistent button sizing.
- Similar actions should be grouped under short section headers and should not repeat unnecessary nouns in every button label.
- Tower-choice controls may use compact symbols or abbreviated labels only if the mapping remains obvious at a glance.
- A deliberate multi-column action layout is allowed if that is the cleanest way to keep grouped controls visible and stationary within the approved sidebar space.
- Shared presentation tokens such as panel framing, header treatment, status badges, and accent usage must stay consistent across the live HUD, pause shell, and defeat shell so the product reads as one authored interface family.

#### Procedures

- Update HUD values every simulation frame or at a readable UI refresh cadence.
- Change button states immediately when affordability changes.
- Change selected-panel contents immediately when the player changes selection.
- Rebuild the contextual action region when selection changes so only relevant controls remain visible.
- Keep the run-status area pinned while contextual controls below it may scroll or page if needed.
- Preserve the command-rail scan order even when shell overlays open; pause and defeat surfaces may summarize or mute details, but they should not invent a contradictory information order.
- On selecting an empty hardpoint, reset contextual action scroll or page state to the first build option.
- On a real harvest-income award, emit the local harvest-result cue and any active tuning telemetry update in the same moment as the coin increase.
- Prefer updating labels, enabled state, and highlight treatment in place rather than repacking controls into visibly shifting vertical positions whenever possible.
- When a selection changes, preserve section shells and spacing even if the action contents inside that group change.

#### Boundaries and Edge Cases

- If no tower is selected, the readiness panel should collapse or show neutral text.
- If the screen becomes crowded, hide low-priority debug counters before hiding core survival information.
- Selecting a tower or hardpoint must never push primary controls off-screen; overflow handling should use a scrollable or paged action region instead of extending one long button column.
- Build controls remaining hidden below the current scroll offset after selecting an empty hardpoint is a usability regression, not acceptable overflow behavior.
- If control labels vary in length, keep the button footprint stable and wrap or compress secondary text before allowing the overall panel layout to jump.

#### Outcomes

- The player should rarely need to guess why a tower is not firing.
- The player should be able to understand loss pressure at a glance.
- The sidebar should feel like a deliberate control panel with hierarchy, not a debug dump of every possible action.

#### Data Requirements

- `coins`
- `corruption_percent`
- `failure_threshold`
- `active_orb_count`
- `shots_fired_recent`
- `selected_tower_status`
- `surge_state`
- `run_state`
- `phase_state`
- `sidebar_sections = status, selected_object, contextual_actions, utility_menu`
- `action_region_overflow_mode`
- `context_action_scroll_reset_on_selection`
- `recent_harvest_event`
- `selected_tower_economy_snapshot`

#### State Machine / Flow

- States: `idle_display`, `selection_display`, `warning_display`, `surge_display`, `empty_hardpoint_actions`, `tower_actions`, `utility_menu`
- Entry triggers: selection change, threshold proximity, surge start
- Exit triggers: deselection, risk reduction, surge end

#### UI / UX Requirements

- A persistent top status area should remain visible at all times.
- Selected-object details should sit in a dedicated panel beneath status.
- Context-sensitive actions should live beneath details and swap cleanly between empty-hardpoint build actions and tower-management actions.
- Utility/menu controls should sit in a quieter region separate from primary gameplay controls.
- The board should remain visually dominant while the sidebar reads as a disciplined support surface rather than an equal-weight second canvas.
- The layout should remain compact, technical, and visually grouped rather than reading as one long stack of equal-priority buttons.
- Similar actions should read as grouped clusters first and individual buttons second.
- Build buttons should prioritize tower identity over repeated verbs, for example a shared `Build` header with short tower-specific labels.
- Upgrade controls should prefer concise labels and consistent placement so the player can build muscle memory instead of rereading the entire stack.
- If one-column presentation cannot keep controls stationary and fully visible, a clean multi-column action region is preferred over a taller unstable single column.
- Selecting an empty hardpoint should immediately surface the build choices without requiring the player to hunt for them below the fold.
- Recent harvest gains should be legible as events, not only inferable from watching the total coin counter.
- Compact harvest attribution should remain in the intended shipped HUD, but expanded per-tower economy detail should appear only contextually in the selected-object panel rather than as a permanent debug strip.
- Live HUD, pause shell, and defeat shell should all look like the same command-console product through shared typography, panel language, and accent behavior.

#### Implementation Notes for Coder

- Keep telemetry modular so tuning-only counters can be removed later without touching core HUD systems.
- Treat this as a layout and interaction refactor, not just a button reorder.
- Treat empty-hardpoint build reachability as a blocking usability defect, not a cosmetic follow-up.

#### Open Questions

- `Recent Harvest` and local harvest popups are part of the intended shipped HUD. Broader orb/shot counters may remain lower-priority and can collapse later only if they materially compete with clearer command-surface presentation.

### 8A. Config-Agnostic Visual Readability and UX Robustness Pass

#### System Name & Goal

- Goal: define UI and visual-polish work that stays correct across wide gameplay-config changes so readability improves without depending on fixed balance values.

#### Core Mechanics

1. UI hierarchy, labels, and feedback timing must remain useful even if costs, HP values, fire rates, orb speeds, or funding thresholds change substantially.
2. Readability should be driven by relative visual states such as `affordable` vs `unaffordable`, `ready` vs `cooldown`, and `low` vs `high` pressure rather than by any one approved numeric table.
3. Moment-to-moment feedback should explain what just happened without requiring the player to memorize current tuning values.
4. The sidebar and HUD should preserve action reachability and scan order at the minimum supported window size, regardless of how many controls or digits current tuning creates.

#### Rules

- Do not assume fixed string lengths for prices, percentages, cooldowns, or funding progress; layout must tolerate larger values and extra digits without overlap or clipping.
- Build, upgrade, mode-swap, and power-funding actions should communicate state through grouping, disabled styling, and concise reason text rather than through memorized costs alone.
- Color should not be the only carrier of important state; pair color with iconography, text, fill amount, pulse, or outline changes so volatile values still read clearly.
- Relative threat communication should use thresholds derived from current live state, not hand-tuned art variants tied to one balance pass.
- Recent-result feedback should prefer "what changed" cues such as gain pips, intensity step-downs, cooldown fill, and funding progress movement over raw number spam.
- Run-status rows should keep a stable top-to-bottom order so scan memory survives tuning churn. The approved MVP order is: `Pressure`, `Phase`, `Corruption`, `Coins`, `Power`, `Level`, `Orb/shot telemetry`, `Recent harvest`, `Surge`, `Run state`.
- `Corruption` and `Power` should use text-plus-bar treatment together rather than bar-only or number-only treatment so both relative state and exact state remain readable across wide value ranges.
- Relative readiness states should use compact named badges such as `STABLE`, `RISING`, `HIGH`, `CRITICAL`, `READY`, and `WAIT` instead of relying on raw numbers alone.
- Unavailable actions should keep their normal action name visible and append a compact in-place reason such as `Need 55c`, `Blocked: power active`, `Select hardpoint`, or `Need stored charge`.
- Success feedback for build, funding, swap, and upgrade actions should appear immediately in the selected-object panel region and describe the completed result, not just clear the disabled state.
- Primary action labels should preserve the verb/object name first and compress secondary cost or reason text second when width becomes tight.
- Empty-hardpoint build reachability remains a blocker even if future tuning adds more buttons, more tower variants, or larger cost numbers.
- Control-panel stability matters as much as raw reachability; a technically reachable control stack that visibly jumps as labels change is not the intended finished behavior for this pass.
- Any visual polish that becomes less readable when values grow or shrink sharply is invalid for this pass, even if it looks better under one tuning snapshot.
- Harvest attribution should converge toward a compact layered cue stack rather than a debug dashboard: keep the local event popup, keep one concise recent-harvest line in status, and keep tower-specific attribution only in contextual selection details.

#### Procedures

- Audit the minimum supported play window using low-cost, high-cost, low-income, and high-income value ranges from current configs to confirm labels and buttons still fit.
- Present run-critical status in fixed priority order: survival pressure first, economy second, selected-object state third, contextual actions fourth, utility last.
- When an action is unavailable, show the same control in-place with a concise failure reason such as insufficient coins, cooldown active, or no stored charge.
- When a meaningful event resolves, update the associated visual cue in the same frame window as the gameplay result: orb impact, harvest gain, corruption telegraph release, mode swap, or funding purchase.
- Prefer compact comparative labels such as bars, segmented pips, and named state badges when they communicate progression more robustly than raw numbers alone.
- Keep the run-status block pinned while selected-object details, contextual actions, and utility controls remain visually separated beneath it.
- Place transient success feedback directly under the selected-object text so it is visible during rapid action chains without displacing the run-status block.
- On build-style and tower-style action labels, preserve the core action text even when cost or failure-reason suffixes wrap.
- Group related actions into stable shells such as `Build`, `Tower Controls`, `Seed Levers`, and `Power`, and prefer changing the contents within a group over inserting new ungrouped controls.
- If a stable single-column stack still causes noticeable jumping or hidden actions at the minimum supported window, switch to a deliberate multi-column action treatment instead of accepting instability.

#### Boundaries and Edge Cases

- If config changes produce four-digit or larger prices, the control layout must remain readable by shrinking secondary text, not by truncating the primary action label.
- If a selected object exposes more actions than the visible panel height allows, the first high-priority action for that selection type must still appear without requiring previous-scroll-position cleanup.
- If tuning lowers values enough that bars or meters move only slightly, add floor visibility rules such as minimum fill or pulse accents so state change still reads.
- If tuning raises values enough that one event causes a large jump, animate the transition quickly but legibly rather than snapping with no causal feedback.
- If multiple feedback events happen together, prioritize corruption danger, tower readiness, and action availability ahead of optional economic detail.
- If a failure reason must be shortened to fit, shorten the reason text first and never replace the base action identity with the reason alone.
- If a power or corruption bar would visually appear empty despite being meaningfully non-zero, enforce a minimum visible fill so the state change still reads.

#### Outcomes

- The player should understand available actions and recent results without relying on one stable balance snapshot.
- The UI should continue to read cleanly after future config edits instead of requiring recurring layout rework.
- Visual polish work in this pass should reduce tuning-coupled regressions, not create new ones.

#### Data Requirements

- `minimum_supported_window = 1280 x 720`
- `ui_value_length_budget`
- `button_label_priority`
- `disabled_action_reason_text`
- `relative_status_badges`
- `funding_progress_visual`
- `recent_result_feedback_duration`
- `minimum_bar_fill_visibility`
- `selection_change_scroll_reset`
- `status_scan_order`
- `success_feedback_text`
- `compact_reason_replacements`
- `action_group_layout_mode`
- `group_header_labels`
- `action_label_abbreviation_rules`

#### State Machine / Flow

- States: `stable_scan`, `selection_changed`, `action_unavailable`, `event_feedback_active`, `overflow_managed`, `warning_emphasis`
- Entry triggers: selection change, affordability change, cooldown change, funding change, corruption-threshold proximity, overflow detected
- Exit triggers: event timeout, state normalization, deselection, overflow resolved

#### UI / UX Requirements

- Status panels should use stable headers and consistent vertical order so players can build scan memory even while values change.
- Build and upgrade controls should keep primary action names readable at all times; cost text is secondary and may compress first.
- Cooldown, readiness, and power-funding progress should have dedicated visual treatments that remain legible without reading exact numbers.
- Recent harvest and cleaning feedback should identify source and effect directionally enough for playtest judgment without requiring full telemetry parsing.
- Readability checks for this pass should explicitly include wide-value-range testing, not just default-config screenshots.
- Disabled actions should explain themselves in the control label or immediately adjacent text rather than forcing the player to click for failure discovery.
- Funding purchases, mode swaps, builds, and upgrades should each emit one short readable confirmation message so outcome clarity does not depend on spotting a numeric delta elsewhere.
- Action groups should keep consistent positions and footprints so status text and controls appear stationary through normal selection changes.
- Shorter labels are preferred over fully spelled repetitive phrasing when the meaning remains unambiguous.

#### Implementation Notes for Coder

- Favor layout rules and reusable visual states over one-off pixel nudges tied to current config values.
- Treat this pass as robustness work for future tuning churn, not as a balance pass.
- Use current config extremes as validation inputs, but do not encode them as permanent assumptions.

#### Open Questions

- No open question for the current MVP pass: keep compact attribution cues and collapse only the debug-like duplication. Ship the local harvest event cue plus concise recent-harvest status, while limiting tower-specific attribution text to selected-object context.

### 8B. Supported-Window Layout and Playfield Framing Pass

#### System Name & Goal

- Goal: lock the remaining GUI follow-up into implementation-ready rules so the supported minimum window keeps core controls reachable and the board reads as a cleanly bounded playfield rather than an overextended canvas.

#### Core Mechanics

1. The sidebar must behave as a fixed control rail with pinned status and utility regions, while only the detail and action bodies are allowed to overflow internally.
2. The minimum supported play window remains `1280 x 720`; at or above that size, core build, upgrade, mode, and power controls must stay visible or immediately reachable inside the structured action region.
3. Selection-detail growth must never steal so much vertical space that the first actionable row for the current context disappears from the supported-window view.
4. The rendered board boundary is the topology `playfield_rect` defined by the approved large-grid perimeter and hardpoint envelope.
5. Space outside that playfield boundary may remain visible as background, but it must not read as additional playable grid space.

#### Rules

- The whole sidebar must not become one scrolling column. `Run Status` and `Menu` remain pinned; only the selection-detail body and contextual-action body may scroll internally if needed.
- At the minimum supported window, the contextual action region must reserve enough visible height to show the active group header plus at least the first actionable row for the current selection type after any required selection-reset behavior.
- Empty-hardpoint selection must still surface the `Build` group at the top of the action region.
- Occupied-hardpoint selection must still surface the first `Tower Controls` row without requiring the player to scroll past the selection text block.
- `Power` controls must remain visible in the structured action region or be reachable within the same action-region scroll context; they must not fall below a whole-sidebar fold created by growing detail text.
- If selection text exceeds its visible budget, handle the overflow inside the selection region by wrap, truncation, or internal scroll before allowing the contextual-action region to lose its minimum visible footprint.
- The supported-window solution should prefer denser grouped controls, shorter secondary text, and deliberate multi-column rows over increasing overall panel height.
- The approved board boundary is the topology `playfield_rect`, not the full canvas width. Grid segments, intensity flashes, and other line-bound visuals must terminate at that boundary instead of implying extra columns on the right edge.
- Hardpoints and temporary effects may visually overlap the board edge slightly for readability, but their anchors must remain on or inside the approved boundary so they do not read as extra board space.
- The approved board-edge treatment is a darker non-playable outer margin plus a subtle cool-toned inset outline aligned to `playfield_rect`; do not use a heavy decorative frame or full-canvas grid continuation.
- Behavior below the declared support floor may degrade gracefully, but any reproduction at or above `1280 x 720` remains a real usability or presentation bug.

#### Procedures

1. On startup, resize, or fullscreen toggle, compute the playfield boundary from topology and treat it as the authoritative rendered board extent.
2. Allocate sidebar height in this priority order: title/status first, utility/menu last, then divide the remaining height between selection details and contextual actions while preserving the action-region visibility floor.
3. When selection changes, rebuild only the relevant action contents inside stable group shells and reset the action-region position as needed for the newly selected context.
4. If the selection block would exceed its height budget, keep the action region stable and resolve the extra detail length inside the selection block itself.
5. During render, ensure line-based visuals are clipped or otherwise confined to the board boundary so the right edge terminates the same way the other sides do.
6. Validate the layout in both default windowed mode and fullscreen, because right-edge drift may change when the canvas width changes.

#### Boundaries and Edge Cases

- If selection text, feedback text, and upgrade preview all become long at once, the action region still keeps its visibility floor; lower-priority detail text should compress first.
- If a selected `Seed Tower` exposes the extra `Seed Levers` group, the first row of tower controls must still remain visible without losing the build-selection reset behavior on empty hardpoints.
- If a future config adds more tower actions or longer reason text, preserve action identity and grouping first; do not solve the overflow by letting the entire sidebar slide off-screen.
- If the canvas is wider than the approved board, the empty space to the right of the board should read as background, not as an extension of the grid.
- If transient effects such as harvest popups, seed pulses, or power highlights approach the edge, they may bleed slightly for readability, but they must originate from in-bounds gameplay anchors.

#### Outcomes

- Supported laptop-sized windows keep the control panel usable without relying on a large display.
- Players can build scan memory because selection-detail growth no longer shoves action groups out of view.
- The board reads as a deliberately framed technical playfield with a consistent right edge instead of a stretched or accidentally expanded grid.

#### Data Requirements

- `minimum_supported_window = 1280 x 720`
- `pinned_sidebar_regions = title, run_status, utility_menu`
- `selection_region_overflow_mode`
- `selection_region_height_budget`
- `contextual_action_visibility_floor`
- `active_group_first_row_visibility`
- `supported_window_validation_cases = empty hardpoint, occupied basic tower, occupied seed tower, active power state`
- `board_boundary_rect = topology.playfield_rect`
- `board_boundary_visual_treatment = darker outer margin + subtle inset outline`
- `line_visual_clip_policy`

#### State Machine / Flow

- States: `supported_window_layout`, `selection_overflow_managed`, `action_floor_preserved`, `board_framed`, `board_resize_recomputed`, `below_support_floor_best_effort`
- Entry triggers: boot, resize, fullscreen toggle, selection change, overflow detected
- Exit triggers: layout recomputed, overflow resolved, deselection, shutdown

#### UI / UX Requirements

- The sidebar must continue to feel like one deliberate control panel, but its internal overflow handling should be invisible to the player during normal use.
- The first actionable controls for the current selection should appear predictably in the same visual area at the support floor.
- Multi-column action rows are preferred whenever they preserve readability and supported-window reachability better than a taller single-column stack.
- The selection section may be information-dense, but it should not dominate the sidebar at the expense of action access.
- The board edge should look intentional and symmetrical; the right side must terminate with the same visual confidence as the left, top, and bottom.

#### Implementation Notes for Coder

- Treat `BUG-021` and `BUG-020` as one layout/framing pass: solve sidebar reachability and board-boundary presentation together so resize behavior is validated once.
- Add targeted regression coverage for supported-window action reachability and right-edge board termination in both default windowed mode and fullscreen where practical.
- Favor layout budgeting and explicit board-boundary rendering rules over one-off pixel nudges.

#### Open Questions

- No open question for the current MVP pass: use the approved darker outer margin plus subtle inset outline treatment. Revisit only if later visual polish proves that cleaner termination alone reads better without losing boundary clarity.

### 8C. Run-State Shell and Session Flow

#### System Name & Goal

- Goal: define the lightweight product shell around the live simulation so `Gridline` launches, pauses, ends, and replays like a coherent game instead of a raw always-live sandbox.

#### Core Mechanics

1. The product opens into a lightweight title/ready shell before the first run starts.
2. The active run can be paused without destroying board context, current selection, or the player's mental model of the current crisis.
3. Defeat transitions into a summary shell that explains why the run ended and what the player can do next.
4. Immediate replay starts a fresh run from the same approved config set without forcing the player through a deep menu stack.
5. Shell screens and overlays reuse the same command-surface visual language as the live HUD.

#### Rules

- MVP shell states are `title_ready`, `active_run`, `paused`, and `defeat_summary`.
- The game must not boot directly into an unframed live run with no start-state context.
- `Esc` from `active_run` opens `paused`; `Esc` from `paused` returns to `active_run`.
- The `paused` shell freezes simulation time, enemy movement, tower cooldown progression, spread cadence, and power-duration countdowns until play resumes.
- The `paused` shell must preserve the underlying board image and the current selection state so the player resumes exactly where they left off.
- The `defeat_summary` shell appears automatically when the loss condition resolves and replaces pause controls with post-run summary plus next actions.
- `Replay` must be the primary post-defeat action and should start a fresh run immediately from the same config without extra confirmation unless the Planner later adds a destructive-profile concern.
- `Quit` and other low-frequency session actions belong to shell surfaces such as `title_ready`, `paused`, or `defeat_summary`; they do not belong in the main contextual action stack.
- The `title_ready` shell should use a dimmed live-board preview as background context rather than a fully opaque menu screen or unrelated splash art.
- The ready-shell background treatment should preserve board identity while clearly reading as pre-run: darken/desaturate the board preview slightly, keep the command-rail shell surfaces crisp above it, and avoid busy overlays that compete with the primary `Start Run` action.
- MVP shell scope is intentionally lean: no save system, no metaprogression, no branching campaign menus, and no settings labyrinth beyond the required display/session actions.

#### Procedures

1. On boot, enter `title_ready` with the board visible as background or preview context plus a primary `Start Run` action.
2. On `Start Run`, initialize a fresh simulation state, clear prior selection and feedback remnants, and enter `active_run`.
3. On `Esc` during `active_run`, freeze simulation updates, preserve current selection/UI context, and open the `paused` shell.
4. On `Resume`, close the pause shell and return to `active_run` with the preserved selection and context intact.
5. On loss, finish the resolving simulation step, snapshot summary data, and transition into `defeat_summary`.
6. On `Replay`, rebuild the run from a fresh state using the current approved config and return to `active_run`.

#### Boundaries and Edge Cases

- If the player pauses during a surge, during an active power window, or while corruption is near the threshold, the shell must preserve those states exactly rather than normalizing them for presentation.
- If defeat occurs during a paused-adjacent input window, defeat takes precedence and the product transitions to `defeat_summary` instead of back to `paused`.
- If the player toggles fullscreen or resizes from a shell state, the shell and board must recompute layout without losing the current run-state identity.
- If a transient event message is active when pause opens, it may be visually muted by the shell, but it must not corrupt or reorder the underlying run state when play resumes.

#### Outcomes

- The game reads as a finished session-based product rather than a tool-like simulation window.
- Players can stop, inspect, lose, and restart runs without confusion or abrupt app-level exits.
- Playtest notes can distinguish shell friction from balance friction because the start, pause, and defeat flows are explicitly defined.

#### Data Requirements

- `run_state = title_ready, active_run, paused, defeat_summary`
- `shell_primary_actions = start_run, resume, replay, fullscreen_toggle, quit`
- `shell_focus_default`
- `pause_preserves_selection = true`
- `pause_freezes_simulation = true`
- `defeat_summary_fields = run_duration, cause_of_loss, highest_phase_reached, corruption_percent_at_loss, highest_power_funding, power_deploy_count`
- `shell_transition_duration`
- `shell_background_treatment = dimmed live-board preview + command-surface scrim`

#### State Machine / Flow

- States: `title_ready`, `active_run`, `paused`, `defeat_summary`
- Entry triggers: boot, start input, `Esc`, loss resolution, replay input
- Exit triggers: start input, resume input, replay input, quit input, shutdown

#### UI / UX Requirements

- The title/ready shell should establish the game's command-console tone quickly without becoming a separate feature-heavy front end.
- The ready shell should show the board as a subdued preview surface behind the command rail so the player immediately reads the product as a live tactical board awaiting activation, not as a disconnected menu scene.
- The pause shell should foreground the immediate decision to resume, restart, or quit while leaving the frozen board visible enough that the player retains situational context.
- The defeat shell must explain the loss in the same visual language as the live HUD and should emphasize the next action rather than trapping the player in a static summary page.
- Summary emphasis order should be: `Cause of loss`, `Run duration`, `Highest phase reached`, `Corruption at loss`, `Power usage`, then optional secondary stats.
- Shell typography, headers, badges, and accent colors should reuse the same visual system as the command rail so the transition between live play and overlays feels intentional and continuous.
- The shell scrim should quiet the background board enough that `Start Run`, `Resume`, and `Replay` remain the obvious primary controls at the support floor without hiding the board completely.

#### Implementation Notes for Coder

- Separate shell state from simulation state so pause and defeat do not require ad hoc gameplay exceptions inside the sim loop.
- Treat replay as a full state reset, not a partial cleanup of the previous run.
- Use the shell to solve session clarity first; do not backfill shell behavior later through one-off keybind hacks.

#### Open Questions

- No open question for the current MVP pass: the ready shell uses a dimmed frozen or near-static live-board preview plus a command-surface scrim. Avoid unrelated splash art and avoid a busy animated attract mode.

## Known Inputs Already Agreed

- Towers use predefined edge hardpoints rather than free placement.
- Hardpoints do not require a separate activation purchase before building.
- If a hardpoint is empty and the player can afford a tower, the player may build directly on that site.
- `game_summary.md` remains source of truth until the Planner promotes a newer decision.
- MVP includes at least three base tower archetypes: `Basic Tower`, `Seed Tower`, and `Burst Tower`.
- Each placed tower keeps its base identity and default behavior.
- Each placed tower may purchase exactly one additional orb behavior during a run at meaningful cost.
- Orb travel uses large, medium, and small line tiers.
- Grid access tier upgrades unlock finer travel layers.
- `grid_access_tier` progression is JSON-configurable.
- Green lines provide harvest income.
- Enemy kills do not provide income.
- Red and green can both spread and intensify.
- Red clears to blue; green harvests to blue.
- Green and red each use three intensity levels.
- If red and green contest the same line at the same time, the current line color remains unchanged.
- Green and red intensity should both read from lighter to darker as level increases.
- Corrupter-focused surges are in MVP; bosses are not.
- Endless escalation must present named landmarks for `Opening Containment`, `Escalation`, and `Critical Load`.
- MVP enemy roster starts with `Corruption Seeder` and `Tower Striker`.
- Orb cleaning is continuous by distance traveled.
- Corruption-capable enemies telegraph impending seeding by shifting from lighter red toward darker red and may pulse on release.
- Meaningful orb impact should produce an immediate visible line-state drop rather than an invisible background-only progress change.
- `fire_rate`, `hp`, `snake_speed`, `hit_damage`, `shot_range`, and `grid_access_tier` are current global upgrade tracks by tower type.
- `hp` applies to both towers and enemies.
- Power tower funding is paid in 10 percent increments and stores one charge at a time.
- Power tower can be deployed onto any hardpoint, including one already occupied by a tower, and restores the prior tower behavior when it expires.
- The product shell includes `title_ready`, `active_run`, `paused`, and `defeat_summary` states.
- `Esc` opens pause during active play and resumes from pause; quitting belongs to shell surfaces rather than the live action stack.
- Each archetype has one fixed secondary behavior option for MVP.
- `Basic Tower -> Guard Mode`, `Seed Tower -> Recall Mode`, `Burst Tower -> Focus Mode`.
- Behavior switching is manual and cooldown-gated.
- `Tower Striker` falls back to an interior corruption-seeding role when no valid tower target exists.
- Tower Striker fallback targeting priority is deterministic: non-red, then centerward, then high-connectivity, then green over blue, then random tie-break.
- While a hardpoint is under power-tower override, only the temporary power state can be damaged; the suspended underlying tower is untargetable and restored intact afterward.
- Power tower is an emergency cleaning-first stabilizer with strong local-to-midfield reach, finest-tier MVP traversal, rapid free output, and a meaningful downside if destroyed early.

## MVP Starter Constants

### 9. Visual Constants

#### System Name & Goal

- Goal: provide an implementation-ready baseline visual spec so the first playable build matches the intended dark technical line-field look without ad hoc choices.

#### Core Mechanics

1. The renderer uses a dark background with layered line tiers, additive glow, and high-contrast state colors.
2. Grid lines remain readable underneath orbs, enemies, and HUD overlays.
3. All values below are starter constants and may be tuned later, but should be used as the default implementation target.

#### Rules

- Use RGBA-style values conceptually even if the renderer stores alpha separately.
- Preserve line readability over decorative bloom.
- Red/green/blue state colors override neutral grid tint on affected segments.

#### Data Requirements

- `background_color = #081018`
- `playfield_overlay_color = #0B1622`
- `board_margin_color = #061019`
- `board_frame_color = #163247`
- `sidebar_color = #0F1726`
- `shell_scrim_color = rgba(6, 12, 18, 0.62)`
- `shell_preview_dim_alpha = 0.38`
- `neutral_large_color = #7FC7FF`
- `neutral_medium_color = #4EA0D8`
- `neutral_small_color = #2A5978`
- `red_level_1 = #7A1E2B`
- `red_level_2 = #B3263A`
- `red_level_3 = #FF425D`
- `green_level_1 = #1F6F4A`
- `green_level_2 = #2BAA63`
- `green_level_3 = #6AF7A3`
- `orb_head_color = #B9F3FF`
- `orb_trail_color = #66D9FF`
- `enemy_seeder_color = #FF7B7B`
- `enemy_striker_color = #FFC16B`
- `warning_color = #FFCC4D`
- `critical_color = #FF5A5A`
- `surge_edge_color = #F2C46D`
- `surge_stinger_color = #FFD36A`
- `corruption_reduction_color = #8EE6FF`
- `corruption_reduction_afterglow = #4FC6D8`
- `large_line_width = 2.5 px`
- `medium_line_width = 1.5 px`
- `small_line_width = 1.0 px`
- `large_alpha = 0.70`
- `medium_alpha = 0.42`
- `small_alpha = 0.24`
- `state_glow_alpha = 0.30`
- `orb_head_radius = 5 px`
- `orb_trail_width = 2 px`
- `hardpoint_radius = 8 px`
- `enemy_radius = 6 px`
- `sidebar_width = 320 px`
- `surge_start_stroke_width = 4 px`
- `surge_persistent_stroke_width = 2 px`
- `corruption_reduction_stroke_width = 3 px`

#### UI / UX Requirements

- Large lines should still read at a glance on a 1920x1080 window.
- Corrupted lines must remain more visually dominant than neutral lines.
- Orbs must read clearly in motion without needing HUD confirmation.

#### Implementation Notes for Coder

- If the engine lacks per-primitive alpha blending, approximate the intended transparency with dimmer hex values rather than dropping the tier hierarchy.

### 10. Grid Topology Constants

#### System Name & Goal

- Goal: define a stable MVP topology so the Coder does not invent map density, hardpoint count, or tier spacing.

#### Core Mechanics

1. MVP uses one rectangular playfield with a right-side UI rail.
2. The line field is generated from fixed tier spacing values.
3. Hardpoints sit on the outer edge of the large-grid boundary.

#### Data Requirements

- `reference_resolution = 1600 x 900`
- `playfield_margin_left = 24 px`
- `playfield_margin_top = 24 px`
- `playfield_margin_bottom = 24 px`
- `playfield_margin_right = sidebar_width + 24 px`
- `large_spacing = 96 px`
- `medium_spacing = 48 px`
- `small_spacing = 24 px`
- `grid_scale_multiplier = 0.5` relative to the earlier coarse prototype baseline
- `target_large_columns = 12`
- `target_large_rows = 8`
- `target_medium_columns = 24`
- `target_medium_rows = 16`
- `target_small_columns = 48`
- `target_small_rows = 32`
- `hardpoint_count = 12`
- `hardpoint_distribution = 3 top, 3 bottom, 3 left, 3 right`
- `hardpoint_anchor_rule = align to large-grid perimeter intersections`

#### Rules

- Hardpoints should be evenly distributed by side, not clustered.
- All movement happens on line segments and intersections generated from this topology.
- Resizing rescales coordinates but does not change logical topology or hardpoint IDs during a run.

#### Implementation Notes for Coder

- If exact column/row count conflicts with dynamic sizing, preserve the spacing first and crop excess boundary space second.

### 11. Timing and Simulation Constants

#### System Name & Goal

- Goal: establish simulation cadence so firing, spread, and movement timings do not drift across systems.

#### Data Requirements

- `simulation_tick_rate = 30 Hz`
- `render_target_fps = 60`
- `fixed_dt = 0.0333 s`
- `hud_refresh_rate = 10 Hz`
- `spread_interval = 0.75 s`
- `green_spread_interval = 1.20 s`
- `shots_recent_window = 1.0 s`
- `behavior_swap_cooldown = 4.0 s`
- `surge_duration = 8.0 s`
- `surge_roll_interval = 12.0 s`
- `level_interval = 45.0 s`

#### Rules

- Simulation should be fixed-step for game-state updates.
- Visual interpolation is optional, but simulation timing is not.
- Cooldowns and lifetimes should resolve in simulation time, not frame count.

### 12. Economy Constants

#### System Name & Goal

- Goal: provide a concrete early-game economy target that supports experimentation without making the first two minutes trivial.

#### Data Requirements

- `starting_coins = 220`
- `behavior_purchase_cost_default = 60`
- `power_funding_chunk_cost = 45`
- `harvest_income_green_1 = 4`
- `harvest_income_green_2 = 8`
- `harvest_income_green_3 = 14`
- `upgrade_cost_fire_rate = 45, 70, 100`
- `upgrade_cost_hp = 40, 65, 95`
- `upgrade_cost_snake_speed = 40, 60, 90`
- `upgrade_cost_hit_damage = 45, 70, 100`
- `upgrade_cost_shot_range = 45, 70, 100`
- `upgrade_cost_grid_access_tier = 80 then 120`

#### Rules

- These are recommended MVP starter values, not final balance.
- Early game should let the player build at least one tower quickly while still leaving room for early experimentation.

### 13. Tower Numeric Table

#### System Name & Goal

- Goal: define coder-ready starter numbers for the three base towers and prevent per-tower guesswork.

#### Core Mechanics

1. Each tower uses a base profile modified by global upgrades and optional secondary mode.
2. Cleaning and damage values are intentionally mixed but role-biased.

#### Data Requirements

- `Basic Tower`
- `build_cost = 55`
- `hp = 120`
- `fire_rate = 1.25 shots/s`
- `shot_cost = 2`
- `snake_speed = 80 px/s`
- `snake_tail_length = 70 px`
- `hit_damage = 10`
- `clean_per_unit_distance = 0.030`
- `harvest_per_unit_distance = 0.022`
- `shot_range = 0` for direct spawn behavior
- `lifetime = 3.2 s`
- `turn_chance = 0.18`
- `grid_access_tier_start = large`
- `Seed Tower`
- `build_cost = 75`
- `hp = 95`
- `fire_rate = 0.65 shots/s`
- `shot_cost = 4`
- `snake_speed = 88 px/s`
- `snake_tail_length = 82 px`
- `hit_damage = 8`
- `clean_per_unit_distance = 0.038`
- `harvest_per_unit_distance = 0.026`
- `shot_range = 340 px`
- `lifetime = 3.8 s`
- `turn_chance = 0.32`
- `grid_access_tier_start = large`
- `Burst Tower`
- `build_cost = 70`
- `hp = 105`
- `fire_rate = 0.90 bursts/s`
- `burst_count = 3`
- `shot_cost = 5 per burst`
- `snake_speed = 92 px/s`
- `snake_tail_length = 52 px`
- `hit_damage = 7`
- `clean_per_unit_distance = 0.020`
- `harvest_per_unit_distance = 0.015`
- `shot_range = 0`
- `lifetime = 2.2 s`
- `turn_chance = 0.48`
- `grid_access_tier_start = large`

#### Rules

- `Burst Tower` pays once per burst, not per individual orb in the burst.
- `Seed Tower` should launch to valid medium/large intersections within range.

### 14. Secondary Mode Numeric Table

#### System Name & Goal

- Goal: define concrete starter overrides for the three named secondary modes.

#### Data Requirements

- `Guard Mode` on `Basic Tower`
- `purchase_cost = 60`
- `swap_cooldown = 4.0 s`
- `fire_rate_multiplier = 1.15`
- `shot_cost_multiplier = 1.0`
- `snake_speed_multiplier = 0.92`
- `clean_multiplier = 0.85`
- `harvest_multiplier = 0.85`
- `damage_multiplier = 1.35`
- `effective_range_cap = 150 px`
- `turn_chance = 0.10`
- `local_defense_radius = 150 px`
- `Recall Mode` on `Seed Tower`
- `purchase_cost = 70`
- `swap_cooldown = 4.0 s`
- `launch_range_override = 160 px`
- `fire_rate_multiplier = 1.10`
- `snake_speed_multiplier = 0.95`
- `clean_multiplier = 0.90`
- `harvest_multiplier = 0.90`
- `damage_multiplier = 1.20`
- `turn_chance = 0.25`
- `local_defense_radius = 160 px`
- `Focus Mode` on `Burst Tower`
- `purchase_cost = 65`
- `swap_cooldown = 4.0 s`
- `burst_count_override = 2`
- `fire_rate_multiplier = 1.00`
- `snake_speed_multiplier = 1.08`
- `clean_multiplier = 1.20`
- `harvest_multiplier = 1.10`
- `damage_multiplier = 1.25`
- `turn_chance = 0.20`
- `forward_bias = 0.70`
- `straight_angle_threshold = 30 degrees`
- `focus_candidate_count = 2`

### 15. Enemy Numeric Table

#### System Name & Goal

- Goal: give the Coder concrete movement and pressure defaults for the MVP enemy roster.

#### Data Requirements

- `Corruption Seeder`
- `hp = 26`
- `speed = 62 px/s`
- `spawn_weight = 0.60 baseline`
- `path_turn_chance = 0.40`
- `path_step_budget = 10 large-segment equivalents`
- `spawn_red_intensity = 2`
- `spawn_red_radius = 1 target segment only`
- `Tower Striker`
- `hp = 34`
- `speed = 74 px/s`
- `spawn_weight = 0.40 baseline`
- `path_turn_chance = 0.22 while converging`
- `tower_contact_damage = 28`
- `fallback_spawn_red_intensity = 2`
- `Spawn scaling`
- `base_spawn_interval = 2.6 s`
- `spawn_interval_floor = 0.8 s`
- `spawn_rate_growth_per_level = 0.10`
- `enemy_hp_growth_per_level = 0.08`

#### Rules

- Baseline spawn composition starts slightly seeder-heavy, then can diversify later through surge rules.

### 16. Corruption and Green Spread Constants

#### System Name & Goal

- Goal: define line-state growth and cleaning thresholds tightly enough for implementation.

#### Data Requirements

- `corruption_failure_threshold = 80 percent`
- `red_clean_threshold_level_1 = 1.0 clean units`
- `red_clean_threshold_level_2 = 2.2 clean units`
- `red_clean_threshold_level_3 = 3.8 clean units`
- `green_harvest_threshold_level_1 = 0.8 harvest units`
- `green_harvest_threshold_level_2 = 1.8 harvest units`
- `green_harvest_threshold_level_3 = 3.0 harvest units`
- `red_spread_chance_large = 0.16`
- `red_spread_chance_medium = 0.12`
- `red_spread_chance_small = 0.08`
- `green_spread_chance_large = 0.09`
- `green_spread_chance_medium = 0.07`
- `green_spread_chance_small = 0.05`
- `red_intensity_growth_chance = 0.22`
- `green_intensity_growth_chance = 0.16`

#### Rules

- Red should spread faster and intensify faster than green.
- Green should still matter enough to be pursued for economy.

### 17. Power Tower Numeric Table

#### System Name & Goal

- Goal: define an implementation-ready emergency power profile without waiting for later balance passes.

#### Data Requirements

- `funding_chunks_required = 10`
- `active_duration = 5.0 s`
- `hp = 140`
- `fire_rate = 6.0 shots/s`
- `shot_cost = 0 during active window`
- `snake_speed = 120 px/s`
- `snake_tail_length = 96 px`
- `hit_damage = 16`
- `clean_per_unit_distance = 0.085`
- `harvest_per_unit_distance = 0.040`
- `shot_range = 280 px`
- `lifetime = 2.8 s`
- `turn_chance = 0.30`
- `grid_access_tier = small`
- `orb_head_radius = 6 px`
- `orb_trail_width = 3 px`

#### Rules

- The power tower should feel immediately superior at stabilization, not subtle.
- It should still be destructible if committed too early or onto a collapsing flank.
- These values are provisional starter defaults for an optional supplemental mechanic; preserving clear funding, readiness, and deploy behavior matters more than reopening deep power retuning during current core-completion work.

### 18. UI Layout Constants

#### System Name & Goal

- Goal: define concrete HUD layout requirements so the first implementation is readable and stable.

#### Data Requirements

- `sidebar_width = 320 px`
- `sidebar_padding = 16 px`
- `button_height = 36 px`
- `button_gap = 8 px`
- `section_gap = 18 px`
- `status_section_min_height = 88 px`
- `selected_object_section_min_height = 120 px`
- `context_action_region = scrollable_or_paged`
- `utility_section_height = 52 px`
- `title_font_size = 22 px`
- `body_font_size = 14 px`
- `small_font_size = 12 px`
- `topbar_height = 56 px`
- `corruption_bar_height = 18 px`

#### Rules

- Top-left HUD: coins, corruption percentage, level timer/progression.
- Right sidebar: persistent status at top, selected-object details beneath, context-sensitive actions beneath details, and separate utility/menu controls at the bottom or in a visually separate footer.
- `New Game` and similar low-frequency controls should not appear inside the main build/upgrade/action stack.
- Build controls appear only for empty hardpoints.
- Tower-management controls appear only for tower selections.
- Power controls remain visually distinct from both.
- Bottom-left optional debug strip: active orbs, shots recent, active enemies.

### 19. Suggested Runtime Architecture

#### System Name & Goal

- Goal: give the Coder a stable implementation outline without dictating exact class names or file boundaries.

#### Core Mechanics

1. Separate simulation state from rendering state.
2. Keep config/constants data-driven.
3. Group logic by responsibility rather than by visual object type alone.

#### Required Responsibilities

- `Config/Spec Loader`
  - Reads constants and gameplay profiles.
  - Validates required keys and ranges.
- `Topology Builder`
  - Builds large/medium/small line graphs.
  - Creates stable IDs for segments, intersections, and hardpoints.
- `Game State / Simulation Core`
  - Owns currencies, timers, level progression, corruption totals, and entity lists.
- `Tower System`
  - Handles tower creation, upgrades, cooldowns, behavior swaps, and firing.
- `Orb System`
  - Spawns orbs, advances line travel, applies continuous cleaning/harvesting, and resolves expiry.
- `Line State System`
  - Tracks blue/green/red state, intensity, spread, conflict resolution, and loss threshold.
- `Enemy System`
  - Spawns enemies, advances pathing, resolves tower targeting and fallback targeting, and applies attacks/corruption creation.
- `Power Tower System`
  - Tracks funding, stored charge, deployment, override state, and restoration.
- `UI Controller`
  - Maps selection and input to actions, build menus, upgrades, and HUD state.
- `Renderer`
  - Draws lines, towers, orbs, enemies, glow, and HUD from read-only simulation data.

#### Suggested Function-Level Surface

- `load_game_spec()`
- `build_topology(rect, spacings, hardpoint_layout)`
- `step_simulation(dt, input_commands)`
- `update_towers(dt)`
- `spawn_orb(...)`
- `advance_orbs(dt)`
- `resolve_line_interactions(dt)`
- `spread_line_states(dt)`
- `spawn_enemies(dt)`
- `advance_enemies(dt)`
- `select_tower_striker_fallback_target()`
- `update_power_tower(dt)`
- `apply_player_action(action)`
- `build_hud_model()`
- `render_frame(surface, hud_model)`

#### Rules

- This is intended guidance, not a required class diagram.
- The Coder should be free to choose classes, ECS, or plain modules as long as these responsibilities remain cleanly separated.

#### Implementation Notes for Coder

- A responsibility outline is useful here and does not step on the Coder's toes because it reduces design drift while leaving structural implementation choices open.
- Avoid hard-wiring numeric constants into logic; keep them in config/spec data where practical.

### 20. Post-MVP Tuning Pass and Playtest Evaluation

#### System Name & Goal

- Goal: define the post-core evaluation lane for pacing, economy pressure, role clarity, and optional power-tower behavior after the command-surface, shell, and core-mechanics presentation work is in a stable finished state.

#### Core Mechanics

1. Treat the MVP starter constants as the baseline and modify only existing values, timings, thresholds, targeting weights, UI grouping, label clarity, and feedback strength during this pass.
2. Focus this pass on pacing, economy pressure, role separation, secondary-mode tradeoffs, and only the optional power-tower timing/value work that remains after core presentation and shell completion.
3. The allowed levers for this pass are existing pacing, economy, power-funding, targeting, and presentation parameters rather than new mechanics or new content classes.
4. Defer any problem that appears to require a new mechanic, new content class, or structural expansion back to Planner instead of growing scope inside this pass.
5. Broader Section 20 evaluation begins only after the current GUI, shell, and readability completion work is stable enough that failures can be attributed to tuning rather than presentation drift.

#### Rules

- No new enemy classes, bosses, tower archetypes, progression layers, currencies, or meta systems may be added in this pass.
- Broader balance-first test cycles should not take priority over missing run-state shell work, escalation-landmark signaling, or command-surface readability work already approved elsewhere in this document.
- Broader Section 20 pacing and power-tower retuning is explicitly off the current MVP critical path until Planner reopens it; `BUG-023` remains deferred while shell, framing, escalation readability, and core tower presentation are completed.
- Do not flatten archetype identity just to hit survival-time targets; role separation is a required outcome, not optional polish.
- Prefer incremental tuning passes over broad multi-system rewrites so playtest results remain attributable.
- Readability/usability work is in scope only when it materially improves decision speed, feedback clarity, or control reachability during live play.
- If a tuning change would alter the game's core fantasy or loop, stop and escalate to Planner.
- When Section 20 work is active, tuning passes should focus on existing-system levers that affect practical power reachability and broader run extension: harvest income, build and upgrade costs, shot costs, spawn/corruption pacing, power-funding chunk cost, and other current timing/value levers already present in the approved systems.
- During current core-completion work, preserve clear funding, deploy, and readiness behavior and non-dominant power usage, but do not treat repeated power deploy viability as a blocker.
- If a new best line becomes rushing power funding so hard that permanent tower development stops mattering, the power tower has become overtuned.
- If runs extend slightly but still never reach a realistic charge or deploy point during a later reopened Section 20 pass, that later batch is incomplete even if secondary modes remain reachable.
- Explicitly defer a green-seeding ally, default medium-grid `Seed Tower` travel, and non-blocking seed-launch-path presentation changes unless Planner reopens scope.
- In informed non-throw play, most losses should land inside the 10 to 15 minute target band.
- Repeated losses before minute 5 indicate the opener is too punishing unless the player is obviously leaving hardpoints idle or refusing affordable actions.
- Repeated sub-minute losses remain unacceptable.
- Repeated survival past minute 18 with stable board control indicates pressure and/or economy tension is too soft.
- By minute 2, the player should usually be able to afford either a second tower or a meaningful first upgrade without being forced into one rigid scripted opener.
- One early experiment such as an early upgrade, behavior purchase, or suboptimal first tower should reduce efficiency but should not by itself create an unrecoverable death spiral.
- `Basic Tower` must remain the most reliable generalist and strongest defensive secondary-mode host.
- `Seed Tower` must remain the strongest remote corruption-response and map-reach tower.
- `Burst Tower` must remain the strongest local interception and panic-control tower.
- If one archetype is clearly best at local defense, remote cleaning, and economy stabilization at the same time, reduce that dominance rather than flattening all three archetypes toward the middle.
- Each secondary mode must solve a real situational weakness while leaving the default mode preferable in at least one common case.
- If a secondary mode is left active almost permanently with no meaningful downside, its tradeoff is too weak.
- If a secondary mode is almost never purchased in long runs, its value or presentation is too weak.
- The power tower must function as an emergency stabilizer that can rescue one collapsing flank or buy a short recovery window, not as a dominant default investment path.
- If optimal play becomes rushing power funding ahead of normal tower network growth in most runs, the power tower is overtuned.
- If players ignore the power tower even when collapsing, it is either undertuned or insufficiently readable.
- At 1280x720-equivalent window space, the player must be able to distinguish low/high red and green intensity, notice an orb-caused line-state step change, read enemy corruption telegraphs, and reach all contextual sidebar controls without hidden critical actions.

#### Procedures

1. Evaluate competent styles such as secondary-first, mixed-then-power, and direct power-rush.
2. For each session, record at minimum: `run_duration`, `cause_of_loss`, `first_secondary_activation_time`, `first_power_funding_purchase_time`, `highest_power_funding_reached`, `charge_stored`, and `power_deploy_count`.
3. Treat a reopened tuning pass as successful only if competent runs can reach at least one meaningful power charge or deploy decision while entering a longer decision window for role separation and late-use judgment.
4. Adjust the smallest allowed existing-system lever first: economy values, pacing/pressure timings, or power-funding values.
5. Re-run the same power-reachability and role-separation lines after each tuning batch before reopening deferred scope ideas.
6. If a fix only works by proposing new mechanics or content classes, defer it back to Planner instead of implementing around the gap.

#### Boundaries and Edge Cases

- A longer run is not automatically a better run; if time-to-loss improves because one tower or mode crowds out the others, the pass has failed role-separation goals.
- A readable but trivial board state is still a failure; readability improvements should support better decisions, not replace pressure.
- If a current task is about shell clarity, board framing, action reachability, or line-readability feedback, solve that directly without reopening the deferred Section 20 power-tower balance lane.
- If economy forgiveness causes shot cost or build order to stop mattering by mid-run, restore pressure before adding more generosity.
- If a build survives longer only because it front-loads one clearly dominant power-rush path, keep tuning until there is real early decision space again.
- If a run can technically charge power only by abandoning basic expansion and then dies before deployment can matter, power reachability is still failing in practice.
- If one of the explicitly deferred scope ideas appears attractive as a shortcut fix, do not implement it without a new planner decision.
- If a sidebar or label change fixes a usability problem without touching balance, prefer that narrower change over rebalance.
- If an issue appears only at small windows or only under dense control sets, treat it as a real usability defect rather than an optional edge polish item.

#### Outcomes

- The build should be ready for longer-form playtesting with clearer pacing expectations and fewer ambiguous balance reads.
- Players should be able to explain why they built a given tower, why they switched modes, and why they deployed or saved the power tower.
- Players and testers should be able to identify the current run phase and the current shell state without guesswork before deeper balance conclusions are trusted.
- Post-run notes should reveal whether a failure came from bad decisions, weak tuning, or unclear feedback instead of mixing all three together.

#### Data Requirements

- `target_run_duration_low = 10 minutes`
- `target_run_duration_high = 15 minutes`
- `power_charge_reachability_gate = at least one meaningful charge or deploy decision should become reachable in competent runs`
- `early_failure_warning_time = 5 minutes`
- `overlong_run_warning_time = 18 minutes`
- `economy_checkpoint_time = 2 minutes`
- `economy_checkpoint_reopen_rule = broader Section 20 lanes stay blocked until the minute-2 checkpoint becomes meaningfully reachable again`
- `economy_checkpoint_success = second tower or meaningful first upgrade is usually affordable`
- `power_tower_target_role = emergency stabilizer`
- `deferred_scope_items = green-seeding ally, default medium-grid seed travel, non-blocking seed-launch-path presentation`
- `minimum_ui_support_window = 1280 x 720`
- `required_readability_checks = red/green intensity readability, visible orb impact step, enemy seeding telegraph clarity, explicit active mode naming, contextual control reachability, active phase readability, run-state shell clarity`
- `playtest_session_notes = run_duration, cause_of_loss, phase_reached, build/upgrade timing, mode usage, power usage, readability/usability pain points`

#### UI / UX Requirements

- The HUD and sidebar must expose enough state for testers to judge pacing, readiness, and pressure without guesswork.
- Active tower behavior must always use explicit mode names such as `Guard Mode`, `Recall Mode`, and `Focus Mode`.
- Run-critical status must stay visible while contextual controls change underneath it.
- Context-sensitive actions must stay reachable under tall control sets and constrained window sizes.
- The player must always be able to tell whether the product is in `active_run`, `paused`, or `defeat_summary`, and what escalation phase the run has reached.
- Readability polish in this pass should focus on decision-relevant signals: line intensity, orb impact, enemy telegraphs, cooldown/readiness state, and power funding/deployment state.

## Approved MVP Defaults

- The MVP Starter Constants in this document are the approved default implementation target for the first playable build.
- The Coder should implement these defaults directly unless the planner-owned source-of-truth docs change.
