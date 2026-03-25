# Game Summary

## High-Level Concept
- Windowed PC grid-based tower defense game with fullscreen toggle.
- Towers fire light orbs with glowing trails.
- Multiple tower archetypes with distinct snake behaviors and per-tower snake parameters.
- The game field is gradually corrupted; corruption is the primary failure pressure.
- Gridlines become visually more corrupted as corruption level rises.
- Light orbs snake along grid lines in random patterns and clean grid lines as they pass.
- Orb path randomness is intentionally uncontrollable and creates tactical uncertainty.
- Other enemy dynamics are possible as well.
- Core fantasy: cleaning and containment under pressure.
- Primary protection target is overall grid integrity; towers are a secondary protection concern.

## Core Gameplay Loop
1. Initialize windowed display (with fullscreen toggle), grid, sidebar UI, glow surface.
2. Spawn enemies continuously with randomized timing.
3. Increase enemy pressure by level over time (primarily spawn count/rate scaling).
4. Spend coins to build towers on predefined hardpoints.
5. Towers fire automatically at a fire rate that can be upgraded, and each shot has a cost.
6. Snakes move along a random grid walk and clean corruption.
7. Balance expansion and per-shot firing costs against corruption and enemy pressure to survive as long as possible.
8. Lose when corruption exceeds 80%.
9. Typical run target: 10 to 15 minutes.
10. Run structure is endless survival.

## Grid and Rendering
- Three grid layers:
  - Large (brightest and boldest), medium (half), small (quarter).
- Orb tails have a fade from head to tail, with glow.
- Orb tails must stay confined to valid grid lines and follow the orb's exact traveled path rather than cutting across cells or using a simplified straight-line approximation.
- Tail visibility should fade progressively from the orb head backward so the oldest portion of the tail is the faintest.
- Map playfield should dynamically scale to fill available screen space (minus UI rail) in both windowed and fullscreen.
- Visual style target remains the provided `Style Example.jpg`: dark technical look, subtle glow, meaningful transparency, and shadowing.
- Grid density/scale is configurable; current direction is to run at half the prior effective grid scale for denser line detail.
- Grid layer widths and brightness should remain clearly differentiated after scaling (large > medium > small).
- See "Style Example.jpg".

## Towers
- Towers use predefined edge hardpoints on the map (not free placement anywhere).
- Hardpoints do not require a separate activation purchase before building.
- If a hardpoint is empty and the player can afford a tower, the player can build directly on that site.
- Tower sell/scrap is not part of MVP.
- MVP includes at least 3 tower archetypes.
- Tower roles vary by design (some stronger at cleaning, others stronger at enemy damage).
- Upgrade paths can shift tower effectiveness between cleaning and damage.
- At placement/build time, the player still chooses one of the base tower archetypes.
- Each placed tower keeps its base identity, role bias, and default orb behavior.
- Each placed tower may purchase exactly one additional orb behavior during a run for a meaningful cost.
- The added behavior is intended to provide situational flexibility, including defensive posture options on vulnerable hardpoints, without erasing the tower's primary role.
- Secondary behavior access should remain a tradeoff against expansion, economy, and raw stat upgrades.
- For MVP scope and archetype clarity, each base tower archetype has one fixed secondary behavior option rather than a broad shared shortlist.
- Switching between a tower's default behavior and purchased secondary behavior is a manual player action and should be cooldown-gated to prevent rapid stance thrashing.
- Initial archetype candidates:
  - Basic Tower: spawns a light orb at the tower with mostly straight, predictable behavior.
  - Seed Tower: fires an orb seed deep into the map; on landing, releases an orb with more random walk.
  - Burst Tower: spawns multiple orbs at the tower with highly random walk and shorter lifespan.
- Planner-locked archetype role bias for MVP:
  - Basic Tower: balanced all-rounder with strongest defensive secondary posture.
  - Seed Tower: strongest long-reach map control and corruption-response tool, weaker local defense by default.
  - Burst Tower: strongest local area denial and enemy interception, weakest sustained long-range coverage.
- Planner-locked fixed secondary behavior mapping for MVP:
  - Basic Tower -> `Guard Mode`: shorter-range, tower-centered defensive behavior that prioritizes local enemy interception and nearby line stabilization over deep cleaning reach.
  - Seed Tower -> `Recall Mode`: replaces deep launch behavior with shorter-range defensive seeding around the hosting hardpoint, creating a local containment posture instead of remote map reach.
  - Burst Tower -> `Focus Mode`: compresses the burst into fewer, more directed shots with better forward reach and cleaner lane pressure, trading away some of the default chaos and close-defense saturation.
- Archetype details are expected to be tuned through playtesting.
- Seed Tower target-selection behavior is auto-targeted but probabilistic and player-adjustable via three levers:
  - `closest_vs_random`: chance to prefer closest valid target vs random target.
  - `red_vs_green`: chance to prioritize red lines vs green lines.
  - `darkest_vs_random`: chance to prioritize darkest/highest-intensity target vs random intensity.
- Initial default lever values:
  - `closest_vs_random`: 70/30
  - `red_vs_green`: 70/30
  - `darkest_vs_random`: 60/40
- For MVP UI/control simplicity, Seed Tower targeting levers should clamp from 0 to 100 in 5-point increments, with each lever displayed as a paired percentage split that always sums to 100.

## Economy
- Start with coins.
- Costs to build towers.
- Towers use per-shot cost (no passive continuous operating drain).
- Costs to upgrade towers (upgrades affect all current and future towers).
- Core strategic tension: survive longer by balancing income and per-shot firing spend.
- Early-game tuning target is forgiving to support experimentation and build exploration.
- Enemy kills do not provide income.
- Income comes from harvesting green gridlines; greener lines are worth more.

## Upgrades
- Sidebar buttons for:
  - `fire_rate`, `hp`, `snake_speed`, `hit_damage`, `shot_range`, `grid_access_tier`
- Upgrade affects all existing and future towers of selected type.
- Buttons show current to next value.
- Upgrade progression is global for the current run (not per individual tower).
- Separate from global stat upgrades, each individual placed tower can buy one additional orb behavior slot/option at a meaningful one-time cost.
- Added behavior access is per tower instance, not a universal unlock for all towers of that type unless later changed explicitly.
- `hp` applies to towers and enemies (not to corruption lines).
- `shot_range` applies to projectile-launching towers (for MVP, Seed Tower and Power Tower behavior as needed).
- `grid_access_tier` controls which grid sizes tower orbs can travel on.

## Orb Movement Access Mechanic
- Default orb behavior starts on `large` grid lines only.
- Per tower type, player can upgrade grid access from:
  - `large` -> `medium` -> `small`
- Higher access tiers allow finer path coverage and cleaning precision.
- This progression is configurable in JSON for tuning.
- Hardpoint spawn behavior should guarantee valid orb emission by snapping to the nearest valid intersection for the current access tier when needed.
- Orb firing should be visually obvious during play, not only detectable via logic/state.

## Corruption System
- Corruption is the primary failure metric.
- Corruption spreads algorithmically outward from already corrupted lines.
- Corruption should be visible and mostly predictable.
- Enemy surges can temporarily create unpredictable spikes in corruption pressure.
- Enemies may create new corruption sites and/or boost corruption spread speed.
- Visual feedback on gridlines reflects current corruption severity.
- Gridline state model:
  - Blue: neutral baseline.
  - Green: harvestable for money; can spread and increase in intensity.
  - Red: corruption; can spread and increase in intensity.
- Both green and red have multiple growth levels.
- Both green and red should use light-to-dark intensity coloring so the player can read at a glance how dense/strong that line state currently is.
- Redder lines require more orb passes to clear.
- Clearing red lines converts them to blue.
- Harvesting/clearing green lines converts them to blue.
- If green and red compete for the same line at the same time, they cancel out and the line remains its current color state.
- Red/green spread should execute across all grid tiers (`large`, `medium`, `small`) with explicit tier-aware spread passes (configurable profile/weights).
- Orb interaction must cause a noticeable visual step on affected lines so the player can immediately see what the orb accomplished. For MVP clarity, an orb pass should visibly knock a corrupted or green line down by one visible color/intensity level whenever progress is meaningfully applied.

## Enemy Pressure Model
- Enemies apply mixed pressure:
  - Directly threatening player structures.
  - Indirectly accelerating corruption through drops, spread boosts, or special attack patterns.
- Enemy behavior variety is a key design lever for difficulty.
- If enemies destroy player structures, towers are lost and must be rebuilt/reactivated.
- Enemies must travel only on valid grid lines/intersections (no free-space diagonal movement through cells).
- Enemies that are about to create corruption should communicate that clearly through color and/or burst feedback before the corruption event resolves.
- Default enemy readability direction: start at a lighter red and darken as they approach corruption release, with an additional brief burst/pulse visual when corruption is actually seeded.
- If a `Tower Striker` has no valid tower target, it should fall back to a corruption-pressure behavior rather than idling: route toward a valid interior line target and create a red corruption source on arrival.
- Tower Striker fallback target priority should be deterministic and pressure-oriented:
  - Prefer non-red interior lines over already-red lines.
  - Prefer targets closer to the playfield center over edge-adjacent lines.
  - Prefer higher-connectivity junctions/segments that can spread pressure broadly.
  - If still tied, prefer green over blue to deny income before selecting randomly among remaining equals.
- This fallback selection should be implemented as ordered priority resolution, not a weighted scoring formula, unless changed later by the Planner.

## Key Systems and Functions (Implementation Notes)
- Main game loop drives all updates and state transitions each frame/tick.
- Orb spawn/launch system uses grid-line movement and landing on medium intersections.
- Grid-walk path generator supports:
  - grid modes: `large`, `medium`, `small`
  - turn chance
  - optional initial direction
  - optional "until exit"
- Orb entity can expire by lifetime or when trail ends.
- Tail length is per tower (`snake_tail_length`).
- Tail rendering should be derived from the orb's real movement history along connected segments so the visible tail matches the exact route recently traveled.

## Controls
- Esc: quit
- Support windowed mode with fullscreen toggle.

## Runtime Telemetry
- HUD should expose clear firing/readability signals for testing and tuning:
  - active orb count
  - shots fired in recent interval (for example, per second)
  - selected tower readiness/cooldown indicator
- For the first playable MVP build, keep these telemetry items visible by default rather than hiding them behind a debug toggle.
- If the project later separates shipping HUD from debug HUD, always-visible HUD items should remain: coins, corruption percentage/failure context, surge state, selected tower readiness/cooldown, and power tower funding/charge status.

## UI Layout Direction
- The right-side UI should behave like a structured control panel, not a single long stack of buttons and text.
- Core run status and selected-object details should remain visible without pushing important actions off-screen.
- The sidebar should support sectioning and overflow management so selecting a tower or hardpoint never makes controls unreachable.
- Preferred layout direction:
  - Persistent top status area for run-critical information.
  - Selected-object details in a dedicated panel beneath status.
  - Context-sensitive action area beneath details for build, upgrade, mode, and seed-targeting controls.
  - Separate utility/menu area for low-frequency actions such as `New Game`, rather than mixing them into the main tower-control stack.
- The main action area should be scrollable or paged if needed, but the design should avoid forcing the player to hunt through an unstructured button column.
- Build controls should appear when an empty hardpoint is selected.
- Tower management controls should appear when a tower is selected.
- Power-tower and utility controls should be visually separated from tower-specific controls.
- The UI should feel sleek and technical: compact, readable, and deliberate, with clear grouping and hierarchy rather than raw button accumulation.
- High-frequency gameplay controls should be prioritized for immediate visibility; low-frequency controls should be moved to a quieter menu/utility region.

## Waves and Milestones
- Milestone waves/events are not required for MVP.
- MVP surge priority: corrupter surge events (enemy behavior focused on accelerating corruption).
- Endless remains the core mode.
- Corrupter surge cadence is random.
- Bosses are explicitly deferred until after the core loop is proven fun.
- Enemy pressure scales by percent growth per level via spawn count/rate increases.

## Special Tower Events
- Player can earn temporary high-power towers with limited duration or availability.
- These are intended as strong momentum swings, distinct from core permanent towers.
- Power tower purchase model:
  - Player can fund progress in chunks (10% at a time).
  - Once fully paid, it can be deployed at any time.
  - Only one stored charge at a time.
  - After use, it can be purchased again.
  - Starting active duration target: 5 seconds (configurable).
  - Shots/actions are free while the power tower is active.
- If a power tower is deployed onto an occupied hardpoint, incoming damage applies to the temporary power tower state only; the underlying permanent tower is suspended and untargetable until the power state ends.
- If the temporary power tower expires naturally or is destroyed early, the underlying permanent tower returns with its pre-power state intact.
- Planner-locked MVP power tower profile:
  - Primary role: emergency stabilization and momentum swing, with cleaning output favored over pure enemy DPS.
  - Coverage: strong local-to-midfield reach from the chosen hardpoint rather than full-map omnipresence.
  - Grid access: should immediately operate on the finest currently intended traversal tier for MVP so it feels meaningfully stronger than most normal towers.
  - Fire pattern: rapid, visually obvious output with no shot-cost pressure during the active window.
  - Damage profile: enough enemy pressure relief to protect a collapsing flank, but not so dominant that it replaces permanent anti-enemy investment.
  - Failure case: if destroyed early, the player still loses the remaining emergency window, so deployment timing matters.

## Open Design Questions (Current)
- The starter numeric tables currently present in `Game_Design.md` are approved as the default implementation target for the first playable MVP build unless the Planner later overrides specific values.
- Post-playtest balance tuning remains open, including whether the approved starter numbers should be raised, lowered, or redistributed after implementation feedback.
- Final visual polish thresholds for sign-off against `Style Example.jpg` (orb prominence, shadow/transparency balance, line subtlety).
