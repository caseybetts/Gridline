# Gridline Game Design

## Document Purpose
This file is the primary design outline for `Gridline`.
It is intended to translate planner-approved decisions into coder-usable feature specifications while `game_summary.md` remains the current source of truth unless the Planner promotes a newer decision here.

## Usage Rules
- Add new mechanics here before or alongside implementation.
- Treat each major gameplay system as its own specification section.
- Prefer explicit rules and edge cases over broad intent statements.
- `game_summary.md` remains the current source of truth unless the Planner explicitly promotes a newer decision into this file.

## Current Product Summary
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
1.

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
- Secondary behavior purchase costs and swap cooldown timings remain open.

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
- Starting numeric profiles per archetype remain open.

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
- Exact purchase costs and per-mode tuning values remain open.

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
- Exact tuning values for each secondary mode remain open.

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

#### Implementation Notes for Coder
- Treat orb travel as line-native movement rather than tile stepping.
- Keep archetype path logic data-driven where possible so tower identities can be tuned without structural rewrites.
- Store enough recent path information to render tails along actual traveled segments instead of reconstructing a shortcut line afterward.

#### Open Questions
- Per-behavior cleaning coefficients and movement profiles still need explicit numeric defaults.

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

#### Procedures
- Build candidate intersection list inside range.
- Resolve targeting pipeline.
- Launch seed toward selected intersection.
- On arrival, snap to exact intersection coordinates and spawn the released orb.

#### Open Questions
- Seed flight visuals may be tuned later, but landing geometry is locked for MVP.

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

#### State Machine / Flow
- States: `solvent`, `constrained`, `broke`
- Entry triggers: start run, spend coins, harvest income
- Exit triggers: income gain, purchase, shot cost payment

#### UI / UX Requirements
- Current coin total must always be visible.
- Disabled actions must clearly indicate insufficient funds.
- Upgrade panels must communicate archetype-wide impact.

#### Implementation Notes for Coder
- Global upgrades should be stored per tower archetype, not per tower instance.

#### Open Questions
- The exact cost curves and stat scaling formulas remain open.

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
- Exact numeric power-state values remain open.

### 8. HUD, Telemetry, and Player Feedback

#### System Name & Goal
- Goal: ensure the player can understand economy, corruption risk, tower activity, and surge state in real time.

#### Core Mechanics
1. The HUD continuously displays run-critical values.
2. The sidebar is the primary interaction surface for purchases, upgrades, and selected-object details.
3. Temporary telemetry is allowed when it improves tuning and readability.

#### Rules
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
- `Esc` quits the run/application.
- Fullscreen toggle support is required.
- In the first playable MVP build, active orb count and recent shots fired remain visible by default rather than being hidden behind a debug-only view.

#### Procedures
- Update HUD values every simulation frame or at a readable UI refresh cadence.
- Change button states immediately when affordability changes.
- Change selected-panel contents immediately when the player changes selection.
- Rebuild the contextual action region when selection changes so only relevant controls remain visible.
- Keep the run-status area pinned while contextual controls below it may scroll or page if needed.

#### Boundaries and Edge Cases
- If no tower is selected, the readiness panel should collapse or show neutral text.
- If the screen becomes crowded, hide low-priority debug counters before hiding core survival information.
- Selecting a tower or hardpoint must never push primary controls off-screen; overflow handling should use a scrollable or paged action region instead of extending one long button column.

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
- `sidebar_sections = status, selected_object, contextual_actions, utility_menu`
- `action_region_overflow_mode`

#### State Machine / Flow
- States: `idle_display`, `selection_display`, `warning_display`, `surge_display`, `empty_hardpoint_actions`, `tower_actions`, `utility_menu`
- Entry triggers: selection change, threshold proximity, surge start
- Exit triggers: deselection, risk reduction, surge end

#### UI / UX Requirements
- A persistent top status area should remain visible at all times.
- Selected-object details should sit in a dedicated panel beneath status.
- Context-sensitive actions should live beneath details and swap cleanly between empty-hardpoint build actions and tower-management actions.
- Utility/menu controls should sit in a quieter region separate from primary gameplay controls.
- The layout should remain compact, technical, and visually grouped rather than reading as one long stack of equal-priority buttons.

#### Implementation Notes for Coder
- Keep telemetry modular so tuning-only counters can be removed later without touching core HUD systems.
- Treat this as a layout and interaction refactor, not just a button reorder.

#### Open Questions
- Which telemetry items should remain in the shipping HUD versus debug-only HUD remains open.

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
- MVP enemy roster starts with `Corruption Seeder` and `Tower Striker`.
- Orb cleaning is continuous by distance traveled.
- Corruption-capable enemies telegraph impending seeding by shifting from lighter red toward darker red and may pulse on release.
- Meaningful orb impact should produce an immediate visible line-state drop rather than an invisible background-only progress change.
- `fire_rate`, `hp`, `snake_speed`, `hit_damage`, `shot_range`, and `grid_access_tier` are current global upgrade tracks by tower type.
- `hp` applies to both towers and enemies.
- Power tower funding is paid in 10 percent increments and stores one charge at a time.
- Power tower can be deployed onto any hardpoint, including one already occupied by a tower, and restores the prior tower behavior when it expires.
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
- `sidebar_color = #0F1726`
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

## Immediate Next Design Work
- Refine values only after coder or playtest feedback shows a concrete problem with the approved MVP defaults.
- Review whether telemetry that is visible in MVP should stay visible in a later shipping-focused pass.
- Revisit visual polish thresholds after the first playable build exists for direct comparison against `Style Example.jpg`.
## Approved MVP Defaults
- The MVP Starter Constants in this document are the approved default implementation target for the first playable build.
- The Coder should implement these defaults directly unless a newer Planner entry overrides them.
