from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from pathlib import Path


TIER_ORDER = ("large", "medium", "small")
TIER_INDEX = {tier: index for index, tier in enumerate(TIER_ORDER)}


@dataclass(frozen=True)
class TowerModeSpec:
    name: str
    purchase_cost: int = 0
    fire_rate_multiplier: float = 1.0
    shot_cost_multiplier: float = 1.0
    snake_speed_multiplier: float = 1.0
    clean_multiplier: float = 1.0
    harvest_multiplier: float = 1.0
    damage_multiplier: float = 1.0
    turn_chance_override: float | None = None
    effective_range_cap: float | None = None
    launch_range_override: float | None = None
    burst_count_override: int | None = None
    forward_bias: float | None = None


@dataclass(frozen=True)
class TowerSpec:
    key: str
    name: str
    build_cost: int
    hp: float
    fire_rate: float
    shot_cost: float
    snake_speed: float
    snake_tail_length: float
    hit_damage: float
    clean_per_unit_distance: float
    harvest_per_unit_distance: float
    shot_range: float
    lifetime: float
    turn_chance: float
    grid_access_tier_start: str
    burst_count: int = 1
    secondary_mode: TowerModeSpec | None = None


@dataclass(frozen=True)
class EnemySpec:
    key: str
    name: str
    hp: float
    speed: float
    spawn_weight: float
    path_turn_chance: float
    tower_contact_damage: float = 0.0
    spawn_red_intensity: int = 0
    path_step_budget: int = 0


@dataclass(frozen=True)
class VisualSpec:
    background: str = "#081018"
    playfield_overlay: str = "#0B1622"
    sidebar: str = "#0F1726"
    neutral_large: str = "#7FC7FF"
    neutral_medium: str = "#4EA0D8"
    neutral_small: str = "#2A5978"
    red_levels: tuple[str, str, str] = ("#FF8FA1", "#D94C64", "#7A1E2B")
    green_levels: tuple[str, str, str] = ("#7EE8B1", "#33B36E", "#175F40")
    orb_head: str = "#B9F3FF"
    orb_trail: str = "#66D9FF"
    enemy_seeder: str = "#FF7B7B"
    enemy_striker: str = "#FFC16B"
    warning: str = "#FFCC4D"
    critical: str = "#FF5A5A"
    text: str = "#D8E5F2"
    muted_text: str = "#89A0B8"
    large_line_width: float = 2.5
    medium_line_width: float = 1.5
    small_line_width: float = 1.0
    orb_head_radius: float = 5.0
    orb_trail_width: float = 2.0
    hardpoint_radius: float = 8.0
    enemy_radius: float = 6.0
    sidebar_width: int = 320


@dataclass(frozen=True)
class GameSpec:
    width: int = 1280
    height: int = 720
    playfield_width: int | None = None
    playfield_height: int | None = None
    playfield_margin_left: int = 24
    playfield_margin_top: int = 24
    playfield_margin_bottom: int = 24
    playfield_margin_right: int = 344
    hardpoint_count: int = 12
    large_spacing: int = 96
    medium_spacing: int = 48
    small_spacing: int = 24
    simulation_tick_rate: int = 30
    hud_refresh_rate: int = 10
    spread_interval: float = 0.75
    green_spread_interval: float = 1.20
    shots_recent_window: float = 1.0
    behavior_swap_cooldown: float = 4.0
    surge_duration: float = 8.0
    surge_roll_interval: float = 12.0
    level_interval: float = 45.0
    starting_coins: int = 220
    power_funding_chunk_cost: int = 45
    upgrade_costs: dict[str, tuple[int, ...]] = field(
        default_factory=lambda: {
            "fire_rate": (45, 70, 100),
            "hp": (40, 65, 95),
            "snake_speed": (40, 60, 90),
            "hit_damage": (45, 70, 100),
            "shot_range": (45, 70, 100),
            "grid_access_tier": (80, 120),
        }
    )
    harvest_income_green: tuple[int, int, int] = (4, 8, 14)
    corruption_failure_threshold: float = 80.0
    red_clean_thresholds: tuple[float, float, float] = (1.0, 2.2, 3.8)
    green_harvest_thresholds: tuple[float, float, float] = (0.8, 1.8, 3.0)
    red_spread_chance_by_tier: dict[str, float] = field(
        default_factory=lambda: {"large": 0.16, "medium": 0.12, "small": 0.08}
    )
    green_spread_chance_by_tier: dict[str, float] = field(
        default_factory=lambda: {"large": 0.09, "medium": 0.07, "small": 0.05}
    )
    red_intensity_growth_chance: float = 0.22
    green_intensity_growth_chance: float = 0.16
    towers: dict[str, TowerSpec] = field(default_factory=dict)
    enemies: dict[str, EnemySpec] = field(default_factory=dict)
    visuals: VisualSpec = field(default_factory=VisualSpec)
    fullscreen_toggle_enabled: bool = True
    power_duration: float = 5.0
    power_hp: float = 140.0
    power_fire_rate: float = 6.0
    power_shot_cost: float = 0.0
    power_snake_speed: float = 120.0
    power_snake_tail_length: float = 96.0
    power_hit_damage: float = 16.0
    power_clean_per_unit_distance: float = 0.085
    power_harvest_per_unit_distance: float = 0.040
    power_shot_range: float = 280.0
    power_lifetime: float = 2.8
    power_turn_chance: float = 0.30
    power_grid_access_tier: str = "small"
    seed_closest_default: int = 70
    seed_red_green_default: int = 70
    seed_darkest_default: int = 60
    base_spawn_interval: float = 2.6
    spawn_interval_floor: float = 0.8
    spawn_rate_growth_per_level: float = 0.10
    enemy_hp_growth_per_level: float = 0.08


def default_spec() -> GameSpec:
    return GameSpec(
        towers={
            "basic_tower": TowerSpec(
                key="basic_tower",
                name="Basic Tower",
                build_cost=55,
                hp=120,
                fire_rate=1.25,
                shot_cost=2,
                snake_speed=80,
                snake_tail_length=70,
                hit_damage=10,
                clean_per_unit_distance=0.030,
                harvest_per_unit_distance=0.022,
                shot_range=0,
                lifetime=3.2,
                turn_chance=0.18,
                grid_access_tier_start="large",
                secondary_mode=TowerModeSpec(
                    name="Guard Mode",
                    purchase_cost=60,
                    fire_rate_multiplier=1.15,
                    snake_speed_multiplier=0.92,
                    clean_multiplier=0.85,
                    harvest_multiplier=0.85,
                    damage_multiplier=1.35,
                    effective_range_cap=150.0,
                ),
            ),
            "seed_tower": TowerSpec(
                key="seed_tower",
                name="Seed Tower",
                build_cost=75,
                hp=95,
                fire_rate=0.65,
                shot_cost=4,
                snake_speed=88,
                snake_tail_length=82,
                hit_damage=8,
                clean_per_unit_distance=0.038,
                harvest_per_unit_distance=0.026,
                shot_range=340,
                lifetime=3.8,
                turn_chance=0.32,
                grid_access_tier_start="large",
                secondary_mode=TowerModeSpec(
                    name="Recall Mode",
                    purchase_cost=70,
                    fire_rate_multiplier=1.10,
                    snake_speed_multiplier=0.95,
                    clean_multiplier=0.90,
                    harvest_multiplier=0.90,
                    damage_multiplier=1.20,
                    turn_chance_override=0.25,
                    launch_range_override=160.0,
                ),
            ),
            "burst_tower": TowerSpec(
                key="burst_tower",
                name="Burst Tower",
                build_cost=70,
                hp=105,
                fire_rate=0.90,
                shot_cost=5,
                snake_speed=92,
                snake_tail_length=52,
                hit_damage=7,
                clean_per_unit_distance=0.020,
                harvest_per_unit_distance=0.015,
                shot_range=0,
                lifetime=2.2,
                turn_chance=0.48,
                grid_access_tier_start="large",
                burst_count=3,
                secondary_mode=TowerModeSpec(
                    name="Focus Mode",
                    purchase_cost=65,
                    snake_speed_multiplier=1.08,
                    clean_multiplier=1.20,
                    harvest_multiplier=1.10,
                    damage_multiplier=1.25,
                    turn_chance_override=0.20,
                    burst_count_override=2,
                    forward_bias=0.70,
                ),
            ),
        },
        enemies={
            "corruption_seeder": EnemySpec(
                key="corruption_seeder",
                name="Corruption Seeder",
                hp=26,
                speed=62,
                spawn_weight=0.60,
                path_turn_chance=0.40,
                spawn_red_intensity=2,
                path_step_budget=10,
            ),
            "tower_striker": EnemySpec(
                key="tower_striker",
                name="Tower Striker",
                hp=34,
                speed=74,
                spawn_weight=0.40,
                path_turn_chance=0.22,
                tower_contact_damage=28,
                spawn_red_intensity=2,
            ),
        },
    )


def load_game_spec(path: str | Path = "game_config.json") -> GameSpec:
    spec = default_spec()
    config_path = Path(path)
    if not config_path.exists():
        return spec
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    display = payload.get("display", {})
    visuals = payload.get("visuals", {})
    palette = visuals.get("palette", {})
    tower_placement = payload.get("tower_placement", {})
    economy = payload.get("economy", {})
    run = payload.get("run", {})
    corruption = payload.get("corruption", {})
    enemies = payload.get("enemies", {})
    surges = payload.get("surges", {})
    power_tower = payload.get("power_tower", {})
    raw_towers = payload.get("towers", [])

    visual_spec = replace(
        spec.visuals,
        background=_rgb_to_hex(palette.get("background"), spec.visuals.background),
        playfield_overlay=_rgb_to_hex(palette.get("panel"), spec.visuals.playfield_overlay),
        sidebar=_rgb_to_hex(palette.get("panel"), spec.visuals.sidebar),
        neutral_large=_tier_blue_hex(palette, "large", spec.visuals.neutral_large),
        neutral_medium=_tier_blue_hex(palette, "medium", spec.visuals.neutral_medium),
        neutral_small=_tier_blue_hex(palette, "small", spec.visuals.neutral_small),
        red_levels=_intensity_hexes(palette, "grid_red", spec.visuals.red_levels),
        green_levels=_intensity_hexes(palette, "grid_green", spec.visuals.green_levels),
        orb_head=_rgb_to_hex(palette.get("orb_head"), spec.visuals.orb_head),
        orb_trail=_rgb_to_hex(palette.get("orb_trail"), spec.visuals.orb_trail),
        enemy_seeder=_rgb_to_hex(palette.get("enemy"), spec.visuals.enemy_seeder),
        enemy_striker=_rgb_to_hex(palette.get("enemy"), spec.visuals.enemy_striker),
        text=_rgb_to_hex(palette.get("text"), spec.visuals.text),
        large_line_width=float(visuals.get("grid_layer_width_by_tier", {}).get("large", spec.visuals.large_line_width)),
        medium_line_width=float(visuals.get("grid_layer_width_by_tier", {}).get("medium", spec.visuals.medium_line_width)),
        small_line_width=float(visuals.get("grid_layer_width_by_tier", {}).get("small", spec.visuals.small_line_width)),
        orb_head_radius=float(visuals.get("orb_head_radius", spec.visuals.orb_head_radius)),
        orb_trail_width=float(visuals.get("orb_trail_width", spec.visuals.orb_trail_width)),
        enemy_radius=float(visuals.get("enemy_radius", spec.visuals.enemy_radius)),
        hardpoint_radius=float(visuals.get("tower_radius", spec.visuals.hardpoint_radius)),
    )

    configured_towers = _load_towers_from_config(raw_towers, spec)
    configured_enemies = _load_enemies_from_config(enemies.get("types", []), spec)
    seed_defaults = _seed_target_defaults(raw_towers, spec)

    spread_interval = float(corruption.get("base_spread_interval_seconds", spec.spread_interval))
    min_spawn = float(enemies.get("random_spawn_interval_min_seconds", spec.spawn_interval_floor))
    max_spawn = float(enemies.get("random_spawn_interval_max_seconds", spec.base_spawn_interval))

    return replace(
        spec,
        width=int(display.get("window_width", spec.width)),
        height=int(display.get("window_height", spec.height)),
        fullscreen_toggle_enabled=bool(display.get("fullscreen_toggle_enabled", spec.fullscreen_toggle_enabled)),
        visuals=visual_spec,
        hardpoint_count=int(tower_placement.get("hardpoint_count", spec.hardpoint_count)),
        starting_coins=int(economy.get("starting_coins", spec.starting_coins)),
        harvest_income_green=tuple(economy.get("green_harvest_income_by_intensity", spec.harvest_income_green)),
        corruption_failure_threshold=float(run.get("corruption_loss_threshold_percent", spec.corruption_failure_threshold)),
        level_interval=float(run.get("level_up_interval_seconds", spec.level_interval)),
        spread_interval=spread_interval,
        green_spread_interval=spread_interval,
        base_spawn_interval=(min_spawn + max_spawn) / 2.0,
        spawn_interval_floor=min_spawn,
        spawn_rate_growth_per_level=float(enemies.get("spawn_count_increase_per_level", spec.spawn_rate_growth_per_level)),
        surge_roll_interval=float(surges.get("random_interval_min_seconds", spec.surge_roll_interval)),
        surge_duration=float(power_tower.get("duration_seconds", spec.surge_duration)),
        power_duration=float(power_tower.get("duration_seconds", spec.power_duration)),
        towers=configured_towers,
        enemies=configured_enemies,
        seed_closest_default=seed_defaults[0],
        seed_red_green_default=seed_defaults[1],
        seed_darkest_default=seed_defaults[2],
    )


def _rgb_to_hex(value: object, fallback: str) -> str:
    if not isinstance(value, list) or len(value) != 3:
        return fallback
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(channel))) for channel in value])


def _tier_blue_hex(palette: dict[str, object], tier: str, fallback: str) -> str:
    explicit_key = f"grid_blue_{tier}"
    if explicit_key in palette:
        return _rgb_to_hex(palette.get(explicit_key), fallback)
    base = palette.get("grid_blue")
    if not isinstance(base, list) or len(base) != 3:
        return fallback
    factor = {"large": 1.35, "medium": 1.0, "small": 0.65}[tier]
    adjusted = [max(0, min(255, round(int(channel) * factor))) for channel in base]
    return "#{:02X}{:02X}{:02X}".format(*adjusted)


def _intensity_hexes(palette: dict[str, object], key: str, fallbacks: tuple[str, str, str]) -> tuple[str, str, str]:
    explicit = tuple(_rgb_to_hex(palette.get(f"{key}_{index}"), "") for index in (1, 2, 3))
    if all(explicit):
        return explicit
    base = palette.get(key)
    if not isinstance(base, list) or len(base) != 3:
        return fallbacks
    channels = [max(0, min(255, int(channel))) for channel in base]
    light = [round(channel + (255 - channel) * 0.42) for channel in channels]
    dark = [round(channel * 0.48) for channel in channels]
    return (
        "#{:02X}{:02X}{:02X}".format(*light),
        "#{:02X}{:02X}{:02X}".format(*channels),
        "#{:02X}{:02X}{:02X}".format(*dark),
    )


def _load_towers_from_config(raw_towers: list[dict[str, object]], spec: GameSpec) -> dict[str, TowerSpec]:
    towers = dict(spec.towers)
    for raw in raw_towers:
        tower_id = str(raw.get("id", ""))
        if tower_id not in towers:
            continue
        current = towers[tower_id]
        towers[tower_id] = replace(
            current,
            name=str(raw.get("display_name", current.name)),
            build_cost=int(raw.get("build_cost", current.build_cost)),
            hp=float(raw.get("base_hp", current.hp)),
            fire_rate=float(raw.get("base_fire_rate", current.fire_rate)),
            shot_cost=float(raw.get("shot_cost", current.shot_cost)),
            snake_speed=_config_speed(float(raw.get("base_snake_speed", current.snake_speed)), current.snake_speed),
            snake_tail_length=float(raw.get("snake_tail_length", current.snake_tail_length)),
            hit_damage=float(raw.get("base_hit_damage", current.hit_damage)),
            shot_range=_config_range(float(raw.get("base_shot_range", current.shot_range)), current.shot_range),
            lifetime=float(raw.get("orb_lifetime_seconds", current.lifetime)),
            turn_chance=_turn_chance_from_behavior(str(raw.get("path_behavior", "")), current.turn_chance),
            grid_access_tier_start=str(raw.get("grid_access_start", current.grid_access_tier_start)),
            burst_count=int(raw.get("burst_count", current.burst_count)),
        )
        if tower_id == "seed_tower":
            seed_targeting = raw.get("seed_targeting", {})
            if isinstance(seed_targeting, dict):
                towers[tower_id] = replace(
                    towers[tower_id],
                    secondary_mode=towers[tower_id].secondary_mode,
                )
    return towers


def _load_enemies_from_config(raw_enemies: list[dict[str, object]], spec: GameSpec) -> dict[str, EnemySpec]:
    if not raw_enemies:
        return spec.enemies
    mapped: dict[str, EnemySpec] = {}
    for raw in raw_enemies:
        attacks_towers = bool(raw.get("attacks_towers", False))
        internal_key = "tower_striker" if attacks_towers else "corruption_seeder"
        current = spec.enemies[internal_key]
        mapped[internal_key] = replace(
            current,
            name=str(raw.get("display_name", current.name)),
            hp=float(raw.get("hp", current.hp)),
        )
    return {**spec.enemies, **mapped}


def _seed_target_defaults(raw_towers: list[dict[str, object]], spec: GameSpec) -> tuple[int, int, int]:
    for raw in raw_towers:
        if str(raw.get("id", "")) != "seed_tower":
            continue
        targeting = raw.get("seed_targeting", {})
        if not isinstance(targeting, dict):
            break
        return (
            int(targeting.get("closest_vs_random_percent", spec.seed_closest_default)),
            int(targeting.get("red_vs_green_percent", spec.seed_red_green_default)),
            int(targeting.get("darkest_vs_random_percent", spec.seed_darkest_default)),
        )
    return (
        spec.seed_closest_default,
        spec.seed_red_green_default,
        spec.seed_darkest_default,
    )


def _config_speed(raw_speed: float, fallback: float) -> float:
    if raw_speed <= 0:
        return fallback
    if raw_speed <= 5.0:
        return fallback * raw_speed
    return raw_speed


def _config_range(raw_range: float, fallback: float) -> float:
    if raw_range <= 0:
        return raw_range
    if raw_range <= 30:
        return raw_range * 24.0
    return raw_range


def _turn_chance_from_behavior(path_behavior: str, fallback: float) -> float:
    mapping = {
        "mostly_straight": 0.18,
        "random_walk": 0.32,
        "high_random_short_life": 0.48,
    }
    return mapping.get(path_behavior, fallback)
