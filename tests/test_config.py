from __future__ import annotations

import unittest
from pathlib import Path

from gridline.config import ConfigError, _validate_config, load_game_config


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_load_default_config(self) -> None:
        config = load_game_config(ROOT / "game_config.json", ROOT / "game_config_schema.json")
        self.assertEqual(config.display["window_width"], 1280)
        self.assertEqual(len(config.towers), 3)

    def test_invalid_hardpoint_cost_count_fails(self) -> None:
        config = load_game_config(ROOT / "game_config.json", ROOT / "game_config_schema.json")
        invalid = dict(config.raw)
        invalid["tower_placement"] = dict(config.raw["tower_placement"])
        invalid["tower_placement"]["activation_cost_by_slot"] = [10]
        with self.assertRaises(ConfigError):
            _validate_config(invalid, load_schema())


def load_schema() -> dict:
    import json

    return json.loads((ROOT / "game_config_schema.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
