from __future__ import annotations

import unittest
from pathlib import Path

from gridline.config import load_game_config
from gridline.sim_line import GameState, LineState


ROOT = Path(__file__).resolve().parents[1]


class SimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_game_config(ROOT / "game_config.json", ROOT / "game_config_schema.json")

    def test_spawn_count_scales_with_level(self) -> None:
        state = GameState(self.config)
        state.level = 5
        self.assertGreaterEqual(state.expected_spawn_count(), 2)

    def test_build_tower_and_fire_consumes_shot_cost(self) -> None:
        state = GameState(self.config)
        built = state.build_tower(0, "basic_tower")
        self.assertTrue(built)
        coins_after_build = state.coins
        state.update(1.0)
        self.assertLess(state.coins, coins_after_build)
        self.assertGreater(len(state.orbs), 0)

    def test_orb_cleans_red_segment(self) -> None:
        state = GameState(self.config)
        key = ("h", 4, 4)
        segment = state.get_segment(key)
        segment.state = LineState.RED
        segment.intensity = 1
        segment.passes_remaining = 1
        state._clean_segment(key)
        self.assertEqual(state.get_segment(key).state, LineState.BLUE)

    def test_grid_access_upgrade_changes_orb_granularity(self) -> None:
        state = GameState(self.config)
        self.assertTrue(state.segment_allowed_for_tier(("h", 3, 4), "large"))
        self.assertFalse(state.segment_allowed_for_tier(("h", 3, 3), "large"))
        self.assertTrue(state.segment_allowed_for_tier(("v", 4, 3), "medium"))
        self.assertFalse(state.segment_allowed_for_tier(("v", 3, 3), "medium"))

    def test_seed_target_respects_range(self) -> None:
        state = GameState(self.config)
        for segment in state.all_segments():
            segment.state = LineState.BLUE
            segment.intensity = 0
            segment.passes_remaining = 0
        near_key = ("h", 10, 0)
        far_key = ("h", 20, 10)
        state.get_segment(near_key).state = LineState.RED
        state.get_segment(near_key).intensity = 2
        state.get_segment(far_key).state = LineState.RED
        state.get_segment(far_key).intensity = 3
        tower_state = state.tower_types["seed_tower"]
        built = state.build_tower(0, "seed_tower")
        self.assertTrue(built)
        target = state._choose_seed_target(state.hardpoints[0].tower)
        self.assertIsNotNone(target)
        distance = ((target[0] - state.hardpoints[0].x) ** 2 + (target[1] - state.hardpoints[0].y) ** 2) ** 0.5
        self.assertLessEqual(distance, tower_state.stat("shot_range"))

    def test_enemy_positions_stay_on_lines(self) -> None:
        state = GameState(self.config)
        state.enemies = [state._spawn_enemy() for _ in range(3)]
        for _ in range(12):
            state._update_enemies(0.25)
            for enemy in state.enemies:
                on_vertical = abs(enemy.x - round(enemy.x)) < 1e-6
                on_horizontal = abs(enemy.y - round(enemy.y)) < 1e-6
                self.assertTrue(on_vertical or on_horizontal)

    def test_all_hardpoints_can_emit_orbs_at_baseline_tier(self) -> None:
        state = GameState(self.config)
        state.coins = 10_000
        for hardpoint in state.hardpoints:
            built = state.build_tower(hardpoint.index, "basic_tower")
            self.assertTrue(built)
            before = len(state.orbs)
            state._fire_tower(hardpoint.tower)
            self.assertGreater(len(state.orbs), before)

    def test_spread_reaches_all_tiers(self) -> None:
        state = GameState(self.config)
        for segment in state.all_segments():
            segment.state = LineState.BLUE
            segment.intensity = 0
            segment.passes_remaining = 0
        state._spread_state(LineState.RED)
        large = any(segment.state == LineState.RED and state.segment_allowed_for_tier(segment.key, "large") for segment in state.all_segments())
        medium = any(segment.state == LineState.RED and state.segment_allowed_for_tier(segment.key, "medium") for segment in state.all_segments())
        small = any(segment.state == LineState.RED and state.segment_allowed_for_tier(segment.key, "small") for segment in state.all_segments())
        self.assertTrue(large)
        self.assertTrue(medium)
        self.assertTrue(small)


if __name__ == "__main__":
    unittest.main()
