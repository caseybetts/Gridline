# Review Tuning Guide

Use this tuning order against `game_config.json` during playtesting.

1. `run.corruption_loss_threshold_percent`
- Higher means easier survival.
- Baseline: `80`; also test `75` and `85`.

2. `enemies.random_spawn_interval_min_seconds` and `enemies.random_spawn_interval_max_seconds`
- Lower values increase enemy pressure sooner.
- This is a primary pacing control.

3. `enemies.spawn_count_increase_per_level`
- Controls long-run difficulty ramp.
- Suggested comparisons: `0.08`, `0.12`, `0.16`.

4. `run.level_up_interval_seconds`
- Smaller values scale difficulty faster.
- Use this to hit the 10 to 15 minute run target.

5. `economy.starting_coins`
- Controls early experimentation space.
- Increase first if early game feels too punishing.

6. `economy.green_harvest_income_by_intensity`
- Main reward loop for containment.
- Increase if players cannot sustain per-shot costs.

7. `towers[*].shot_cost`
- Primary economic pressure for tower use.
- Increase Burst shot cost first if Burst dominates.

8. `towers[*].base_fire_rate` and `towers[*].base_hit_damage`
- Core combat balance knobs.
- Change one tower at a time for clean signal.

9. `towers[*].base_snake_speed` and `towers[*].orb_lifetime_seconds`
- Controls coverage and cleaning reach.
- Use these to strengthen tower role identity.

10. `corruption.base_spread_interval_seconds`
- Lower values increase corruption spread speed.
- Tune this after economy/enemy balance is stable.

11. `surges.random_interval_min_seconds` and `surges.random_interval_max_seconds`
- Wider intervals reduce chaos and make pressure more readable.

12. `power_tower.duration_seconds`
- Tunes emergency recovery strength.
- Keep short (about 5 to 7 seconds) to preserve core loop value.

## Testing Workflow

1. Change only 1 to 2 values per run.
2. Log time-to-loss and peak corruption.
3. Run each setting at least 3 times before concluding.
4. Tune in this sequence: early economy, then difficulty ramp, then surge chaos.
