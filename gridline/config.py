from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


GRID_ACCESS_ORDER = {"large": 0, "medium": 1, "small": 2}


class ConfigError(ValueError):
    """Raised when the game config is missing or invalid."""


@dataclass(frozen=True)
class GameConfig:
    raw: dict[str, Any]
    source_path: Path

    @property
    def display(self) -> dict[str, Any]:
        return self.raw["display"]

    @property
    def towers(self) -> list[dict[str, Any]]:
        return self.raw["towers"]

    @property
    def enemies(self) -> dict[str, Any]:
        return self.raw["enemies"]


def load_game_config(
    config_path: str | Path = "game_config.json",
    schema_path: str | Path = "game_config_schema.json",
) -> GameConfig:
    config_file = Path(config_path)
    schema_file = Path(schema_path)
    if not config_file.exists():
        raise ConfigError(f"Missing config file: {config_file}")
    if not schema_file.exists():
        raise ConfigError(f"Missing schema file: {schema_file}")

    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in schema file {schema_file}: {exc}") from exc

    try:
        raw = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file {config_file}: {exc}") from exc

    _validate_schema_shape(schema)
    _validate_config(raw, schema)
    return GameConfig(raw=raw, source_path=config_file)


def _validate_schema_shape(schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ConfigError("Schema must describe a root object.")
    if "properties" not in schema or "required" not in schema:
        raise ConfigError("Schema must include root properties and required lists.")


def _validate_config(config: dict[str, Any], schema: dict[str, Any]) -> None:
    required = schema["required"]
    properties = schema["properties"]
    _expect_object("root", config)
    _validate_required_keys("root", config, required)
    _reject_extra_keys("root", config, properties)

    for key in required:
        _validate_value(f"root.{key}", config[key], properties[key])

    grid = config["grid"]
    economy = config["economy"]
    tower_placement = config["tower_placement"]
    towers = config["towers"]
    enemies = config["enemies"]

    intensity_levels = grid["intensity_levels"]
    if len(grid["red_to_blue_passes_by_intensity"]) != intensity_levels:
        raise ConfigError("grid.red_to_blue_passes_by_intensity length must match grid.intensity_levels.")
    if len(grid["green_to_blue_passes_by_intensity"]) != intensity_levels:
        raise ConfigError("grid.green_to_blue_passes_by_intensity length must match grid.intensity_levels.")
    if len(economy["green_harvest_income_by_intensity"]) != intensity_levels:
        raise ConfigError("economy.green_harvest_income_by_intensity length must match grid.intensity_levels.")
    if len(tower_placement["activation_cost_by_slot"]) != tower_placement["hardpoint_count"]:
        raise ConfigError("tower_placement.activation_cost_by_slot length must match tower_placement.hardpoint_count.")
    if enemies["random_spawn_interval_min_seconds"] > enemies["random_spawn_interval_max_seconds"]:
        raise ConfigError("enemies random spawn min interval cannot exceed max interval.")

    surge = config["surges"]
    if surge["enabled"] and (
        surge.get("random_interval_min_seconds") is None or surge.get("random_interval_max_seconds") is None
    ):
        raise ConfigError("surges enabled requires random interval min and max values.")
    if surge["enabled"] and surge["random_interval_min_seconds"] > surge["random_interval_max_seconds"]:
        raise ConfigError("surges random interval min cannot exceed max.")

    seen_tower_ids: set[str] = set()
    for tower in towers:
        tower_id = tower["id"]
        if tower_id in seen_tower_ids:
            raise ConfigError(f"Duplicate tower id: {tower_id}")
        seen_tower_ids.add(tower_id)

        start = GRID_ACCESS_ORDER[tower["grid_access_start"]]
        max_tier = GRID_ACCESS_ORDER[tower["grid_access_max"]]
        if start > max_tier:
            raise ConfigError(f"Tower {tower_id} grid access start cannot exceed max tier.")
        if tower["emission_mode"] == "projectile_seed" and "seed_targeting" not in tower:
            raise ConfigError(f"Tower {tower_id} requires seed_targeting for projectile_seed emission mode.")
        if tower["path_behavior"] == "high_random_short_life" and "burst_count" not in tower:
            raise ConfigError(f"Tower {tower_id} requires burst_count for high_random_short_life behavior.")
        if tower["id"] == "seed_tower" and tower["base_shot_range"] <= 0:
            raise ConfigError("seed_tower must have a positive base_shot_range.")

    seen_enemy_ids: set[str] = set()
    for enemy in enemies["types"]:
        enemy_id = enemy["id"]
        if enemy_id in seen_enemy_ids:
            raise ConfigError(f"Duplicate enemy id: {enemy_id}")
        seen_enemy_ids.add(enemy_id)


def _validate_value(path: str, value: Any, schema: dict[str, Any]) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        _expect_object(path, value)
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        _validate_required_keys(path, value, required)
        if schema.get("additionalProperties") is False:
            _reject_extra_keys(path, value, properties)
        for key in required:
            _validate_value(f"{path}.{key}", value[key], properties[key])
        for key, child in properties.items():
            if key in value and key not in required:
                _validate_value(f"{path}.{key}", value[key], child)
        return

    if schema_type == "array":
        if not isinstance(value, list):
            raise ConfigError(f"{path} must be an array.")
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(value) < min_items:
            raise ConfigError(f"{path} must contain at least {min_items} items.")
        if max_items is not None and len(value) > max_items:
            raise ConfigError(f"{path} must contain at most {max_items} items.")
        if schema.get("uniqueItems") and len(value) != len(set(value)):
            raise ConfigError(f"{path} items must be unique.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_value(f"{path}[{index}]", item, item_schema)
        return

    if schema_type == "string":
        if not isinstance(value, str):
            raise ConfigError(f"{path} must be a string.")
        _validate_enum(path, value, schema)
        return

    if schema_type == "boolean":
        if not isinstance(value, bool):
            raise ConfigError(f"{path} must be a boolean.")
        return

    if schema_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{path} must be an integer.")
        _validate_number_bounds(path, value, schema)
        _validate_enum(path, value, schema)
        return

    if schema_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{path} must be a number.")
        _validate_number_bounds(path, float(value), schema)
        _validate_enum(path, value, schema)
        return

    raise ConfigError(f"{path} uses unsupported schema type {schema_type!r}.")


def _validate_required_keys(path: str, value: dict[str, Any], required: list[str]) -> None:
    missing = [key for key in required if key not in value]
    if missing:
        raise ConfigError(f"{path} is missing required keys: {', '.join(missing)}")


def _reject_extra_keys(path: str, value: dict[str, Any], properties: dict[str, Any]) -> None:
    extras = sorted(set(value) - set(properties))
    if extras:
        raise ConfigError(f"{path} contains unsupported keys: {', '.join(extras)}")


def _expect_object(path: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must be an object.")


def _validate_number_bounds(path: str, value: float, schema: dict[str, Any]) -> None:
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_minimum = schema.get("exclusiveMinimum")
    if minimum is not None and value < minimum:
        raise ConfigError(f"{path} must be >= {minimum}.")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{path} must be <= {maximum}.")
    if exclusive_minimum is not None and value <= exclusive_minimum:
        raise ConfigError(f"{path} must be > {exclusive_minimum}.")


def _validate_enum(path: str, value: Any, schema: dict[str, Any]) -> None:
    allowed = schema.get("enum")
    if allowed is not None and value not in allowed:
        raise ConfigError(f"{path} must be one of {allowed}.")
