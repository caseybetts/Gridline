# Game Summary

## Vision Statement
- Endless PC tower defense about containing corruption across a glowing grid network with partially unpredictable light-orb routing.

## High-Level Concept
- Platform: PC, windowed by default with fullscreen toggle.
- Genre: grid-based tower defense / corruption containment.
- Mode: endless survival.
- Core fantasy: cleaning and containment under pressure.
- Primary protection target: overall grid integrity; towers are secondary assets.
- Visual direction: dark technical presentation with readable glow, bounded playfield framing, and line-based motion clarity.
- Exact mechanic rules, constants, and procedures live in `Game_Design.md`.

## Core Pillars
- Containment under pressure.
- Tactical uncertainty from stochastic orb paths.
- Distinct edge-hardpoint tower roles with meaningful secondary stances.
- Economy tension between expansion, upgrades, and per-shot spend.
- Stable, readable control-panel UX on supported window sizes.

## Feature List
- Multi-tier grid rendering and line-bound orb travel.
- Corruption and green-line state systems.
- Edge hardpoint build system with three MVP tower archetypes.
- Global upgrades and harvest-driven economy.
- Per-tower secondary behavior unlocks with manual mode switching.
- Enemy pressure and surge events.
- Optional temporary power-tower event that may be deferred without breaking the core loop.
- Player-facing telemetry and structured sidebar controls.
- Run-state shell covering start, pause, defeat summary, and immediate replay flow.
- Strong visual event language for corruption growth, cleansing, harvest gain, surges, and power deployment.
- Readable endless-run escalation landmarks so early, mid, and late pressure phases feel intentional rather than formless.

## Core Gameplay Loop
1. Start a run with coins, an active grid, and empty edge hardpoints.
2. Build towers and buy global upgrades.
3. Towers automatically fire light orbs along valid grid lines.
4. Orbs clean corruption, harvest green lines, and help preserve board integrity.
5. Balance economy, coverage, and firing spend as enemy pressure rises.
6. Lose when corruption exceeds the fail threshold.

## Major System Direction
- Grid and rendering: the game must read as line-based, not cell-based; orb tails should match real traveled paths; final visual sign-off should maintain a sleek technical finish.
- Towers: MVP centers on `Basic`, `Seed`, and `Burst` roles. Each keeps one fixed planner-approved secondary pairing so archetype identity stays clear. See `Game_Design.md` for exact behavior.
- Economy and upgrades: income comes from harvesting green lines rather than enemy kills, and the player should feel real tension between expansion, upgrades, shot spend, and optional mode unlocks.
- Orb access and pathing: traversal begins on broader grid tiers and upgrades into finer coverage. Edge hardpoints must still create meaningful interior influence; persistent perimeter-skimming is not acceptable as a settled behavior.
- Enemy pressure: enemies should threaten both towers and corruption state while staying visibly line-bound and telegraphing corruption-seeding behavior.
- UI and telemetry: the right-rail control panel should stay structured, visually stable, and reachable on supported laptop-sized windows. Core build, upgrade, mode, and power actions must remain visible or immediately reachable.
- Power tower: this is an optional supplemental mechanic rather than a core pillar. It may add a late-run momentum swing when present, but it must not block completion of the core tower game, shell, escalation read, or visual finish.
- Session shell: the game should present as a coherent command-console product rather than a raw simulation sandbox, with clear start-of-run, in-run, pause, and loss-state framing.
- Visual finish: board framing, tower states, corruption states, orb motion, alerts, and sidebar typography should share one intentional visual language instead of reading like separate debug layers.
- Escalation structure: endless mode still needs explicit early, mid, and late pressure landmarks so players can feel progression and the team can judge feature completeness before deep balance work.

## High-Level UX Direction
- The board is the hero surface, with the sidebar acting as a stable command rail rather than a scrolling dump of controls.
- The player should be able to read the current crisis in this order: board health and corruption spread, imminent threat or surge, selected-tower action options, then economy and power status.
- Visual cues for corruption danger, successful cleansing, harvest gain, mode switching, and power activation must be distinct at a glance instead of relying on subtle text changes.
- The supported-window presentation should feel sharp, authored, and game-like, not merely functional.

## Session Structure
- Start flow: the player should enter through a simple command-center shell that frames the run, exposes the primary play action immediately, and keeps low-frequency settings secondary.
- In-run flow: the player should always understand whether they are actively defending, briefly pausing to assess, or reacting to a named surge/crisis moment.
- Pause flow: pausing should preserve situational readability, provide quick access to resume or restart, and avoid feeling like a debug interruption.
- Defeat flow: loss should transition into a concise run summary that explains how long the defense held, why the grid failed, and invites an immediate replay.
- Replay flow: restarting a run should be friction-light so the endless format feels intentionally replayable rather than menu-heavy.

## Escalation Structure
- Early phase: establish footholds, learn the opening pressure, and make the first meaningful build-versus-upgrade decisions without immediate chaos.
- Mid phase: the board should widen into real multi-front containment, with surges, secondary modes, and power timing becoming readable strategic tools rather than hidden edge cases.
- Late phase: the run should become a recognizable crisis-management state with layered threats, harder tradeoffs, and stronger audiovisual intensity, but still remain legible enough that losses feel attributable.
- Phase transitions should be readable through combined pressure, visuals, and telemetry rather than by invisible numeric thresholds alone.

## Presentation Priorities
- Playfield clarity first: the board frame, active lines, corruption spread, tower ownership, and current emergencies must read cleanly before secondary telemetry details compete for attention.
- Unified visual language: typography, panel shells, line glow, tower highlights, alerts, and power-state treatment should look authored as one product family.
- Motion with purpose: orb travel, corruption growth, cleaning events, and surge alerts should feel crisp and directional, not like generic flashes or placeholder debug effects.
- Event emphasis: major moments such as surge starts, power deployment, tower loss, and recovery swings should have enough visual weight to punctuate the run.
- Supported-window discipline: polish choices must hold at the minimum supported window instead of only looking good at spacious desktop sizes.

## Roadmap Milestones
1. Planning completion: lock the missing high-level product decisions for session flow, escalation landmarks, and presentation priorities so implementation stops drifting into balance-only loops.
2. Presentation completion: bring the GUI, playfield framing, event feedback, and overall visual hierarchy up to a polished baseline that matches the game's intended identity.
3. Gameplay completion: ensure every planner-approved major system and player-facing flow is implemented and readable in live play, including the shell around starting, pausing, losing, and replaying runs.
4. Balance and validation: only after the design and presentation milestones are met should longer-form tuning, feel testing, and balance-driven regression cycles become the primary focus.

## Risk Assessment
- The current biggest project risk is spending more cycles on tuning a build whose presentation and player-facing shell are still incomplete.
- Endless mode can feel directionless if escalation landmarks are not defined clearly enough for both players and developers to read the run's changing phases.
- GUI polish can turn into low-value micro-adjustment unless the project first locks the intended visual hierarchy and command-surface identity.
- Optional systems such as the power tower should not pull the team back into balance loops before the core GUI, shell, and tower-mechanics presentation is fully locked.
- Adding new features without guarding the core pillars would create scope creep; additions should strengthen containment pressure, role clarity, and readable decision-making rather than widen the game sideways.
