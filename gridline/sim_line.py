from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import math
import random
from typing import Iterable

from gridline.config import GRID_ACCESS_ORDER, GameConfig


class LineState(str, Enum):
    BLUE = "blue"
    GREEN = "green"
    RED = "red"


@dataclass
class LineSegment:
    orientation: str
    x: int
    y: int
    state: LineState = LineState.BLUE
    intensity: int = 0
    passes_remaining: int = 0

    @property
    def key(self) -> tuple[str, int, int]:
        return (self.orientation, self.x, self.y)

    @property
    def midpoint(self) -> tuple[float, float]:
        if self.orientation == "h":
            return (self.x + 0.5, float(self.y))
        return (float(self.x), self.y + 0.5)


@dataclass
class Hardpoint:
    index: int
    x: float
    y: float
    activation_cost: int
    tower_type_id: str | None = None
    tower: Tower | None = None


@dataclass
class TowerTypeState:
    config: dict
    upgrade_levels: dict[str, int] = field(
        default_factory=lambda: {
            "fire_rate": 0,
            "hp": 0,
            "snake_speed": 0,
            "hit_damage": 0,
            "shot_range": 0,
            "grid_access_tier": 0,
        }
    )

    def stat(self, key: str) -> float:
        level = self.upgrade_levels[key]
        base_key = {
            "fire_rate": "base_fire_rate",
            "hp": "base_hp",
            "snake_speed": "base_snake_speed",
            "hit_damage": "base_hit_damage",
            "shot_range": "base_shot_range",
        }[key]
        base_value = float(self.config[base_key])
        scale = {
            "fire_rate": 0.12,
            "hp": 0.15,
            "snake_speed": 0.10,
            "hit_damage": 0.18,
            "shot_range": 0.20,
        }[key]
        return round(base_value * (1.0 + scale * level), 4)

    def grid_access_tier(self) -> str:
        start_idx = GRID_ACCESS_ORDER[self.config["grid_access_start"]]
        max_idx = GRID_ACCESS_ORDER[self.config["grid_access_max"]]
        current_idx = min(max_idx, start_idx + self.upgrade_levels["grid_access_tier"])
        return ("large", "medium", "small")[current_idx]

    def upgrade_cost(self, key: str, cost_curve_multiplier: float) -> int:
        base_cost = max(25, int(self.config["build_cost"] * 0.5))
        return int(round(base_cost * (cost_curve_multiplier ** self.upgrade_levels[key])))


@dataclass
class Tower:
    type_state: TowerTypeState
    hardpoint: Hardpoint
    cooldown: float = 0.0
    hp: float = 0.0

    def __post_init__(self) -> None:
        self.hp = self.type_state.stat("hp")


@dataclass
class Orb:
    x: float
    y: float
    dx: int
    dy: int
    life_remaining: float
    speed: float
    damage: float
    tail_length: int
    turn_chance: float
    access_tier: str
    trail: deque[tuple[float, float]] = field(default_factory=deque)


@dataclass
class Enemy:
    enemy_id: str
    x: float
    y: float
    dx: int
    dy: int
    hp: float
    speed: float
    attacks_towers: bool
    corruption_behavior: str


@dataclass
class PowerTowerState:
    funding_percent: int = 0
    charged: bool = False
    active_time_remaining: float = 0.0


class GameState:
    def __init__(self, config: GameConfig, seed: int = 7):
        self.config = config
        self.random = random.Random(seed)
        self.grid_width = 24
        self.grid_height = 14
        self.max_x = self.grid_width - 1
        self.max_y = self.grid_height - 1
        self.level = 1
        self.level_timer = 0.0
        self.spawn_timer = self._roll_spawn_interval()
        self.surge_timer = self._roll_surge_interval()
        self.surge_time_remaining = 0.0
        self.shots_fired_this_second = 0
        self.shot_counter_timer = 0.0
        self.corruption_timer = config.raw["corruption"]["base_spread_interval_seconds"]
        self.green_timer = 2.5
        self.coins = config.raw["economy"]["starting_coins"]
        self.loss = False
        self.selected_tower_type_id = config.raw["towers"][0]["id"]
        self.selected_upgrade = "fire_rate"
        self.power_tower = PowerTowerState()
        self.orbs: list[Orb] = []
        self.enemies: list[Enemy] = []
        self.tower_types = {tower["id"]: TowerTypeState(config=tower) for tower in config.raw["towers"]}
        self.h_segments = {
            (x, y): LineSegment("h", x, y) for y in range(self.grid_height) for x in range(self.grid_width - 1)
        }
        self.v_segments = {
            (x, y): LineSegment("v", x, y) for x in range(self.grid_width) for y in range(self.grid_height - 1)
        }
        self.hardpoints = self._build_hardpoints()
        self._seed_initial_lines()

    def spread_profile(self) -> dict[str, int]:
        profile = self.config.raw.get("spread_profile_by_tier")
        if profile:
            return {
                "large": int(profile.get("large", 1)),
                "medium": int(profile.get("medium", 1)),
                "small": int(profile.get("small", 1)),
            }
        return {"large": 1, "medium": 1, "small": 1}

    def all_segments(self) -> list[LineSegment]:
        return list(self.h_segments.values()) + list(self.v_segments.values())

    def active_segments(self) -> Iterable[LineSegment]:
        return (segment for segment in self.all_segments() if segment.state != LineState.BLUE)

    def get_segment(self, key: tuple[str, int, int]) -> LineSegment:
        orientation, x, y = key
        return self.h_segments[(x, y)] if orientation == "h" else self.v_segments[(x, y)]

    def layer_spacing(self, tier: str) -> int:
        return {"large": 4, "medium": 2, "small": 1}[tier]

    def _seed_initial_lines(self) -> None:
        segments = self.all_segments()
        for _ in range(26):
            self._increase_segment(self.random.choice(segments).key, LineState.GREEN)
        for _ in range(18):
            self._increase_segment(self.random.choice(segments).key, LineState.RED)

    def _build_hardpoints(self) -> list[Hardpoint]:
        count = self.config.raw["tower_placement"]["hardpoint_count"]
        activation_costs = self.config.raw["tower_placement"]["activation_cost_by_slot"]
        points = []
        for index in range(count):
            t = index / count
            perimeter = t * 4
            if perimeter < 1:
                points.append((perimeter * self.max_x, 0))
            elif perimeter < 2:
                points.append((self.max_x, (perimeter - 1) * self.max_y))
            elif perimeter < 3:
                points.append(((3 - perimeter) * self.max_x, self.max_y))
            else:
                points.append((0, (4 - perimeter) * self.max_y))
        return [
            Hardpoint(index=i, x=float(round(x)), y=float(round(y)), activation_cost=activation_costs[i])
            for i, (x, y) in enumerate(points)
        ]

    def _roll_spawn_interval(self) -> float:
        enemies = self.config.raw["enemies"]
        return self.random.uniform(enemies["random_spawn_interval_min_seconds"], enemies["random_spawn_interval_max_seconds"])

    def _roll_surge_interval(self) -> float:
        surges = self.config.raw["surges"]
        if not surges["enabled"]:
            return math.inf
        return self.random.uniform(surges["random_interval_min_seconds"], surges["random_interval_max_seconds"])

    def build_tower(self, hardpoint_index: int, tower_type_id: str | None = None) -> bool:
        tower_type_id = tower_type_id or self.selected_tower_type_id
        hardpoint = self.hardpoints[hardpoint_index]
        if hardpoint.tower is not None:
            return False
        tower_cfg = self.tower_types[tower_type_id].config
        total_cost = hardpoint.activation_cost + tower_cfg["build_cost"]
        if self.coins < total_cost:
            return False
        self.coins -= total_cost
        hardpoint.tower_type_id = tower_type_id
        hardpoint.tower = Tower(type_state=self.tower_types[tower_type_id], hardpoint=hardpoint)
        return True

    def upgrade_selected_tower_type(self, upgrade_key: str | None = None) -> bool:
        upgrade_key = upgrade_key or self.selected_upgrade
        state = self.tower_types[self.selected_tower_type_id]
        cost = state.upgrade_cost(upgrade_key, self.config.raw["upgrades"]["cost_curve_multiplier"])
        if self.coins < cost:
            return False
        self.coins -= cost
        state.upgrade_levels[upgrade_key] += 1
        if upgrade_key == "hp":
            for hardpoint in self.hardpoints:
                if hardpoint.tower and hardpoint.tower.type_state is state:
                    hardpoint.tower.hp = state.stat("hp")
        return True

    def fund_power_tower(self) -> bool:
        cfg = self.config.raw["power_tower"]
        if not cfg["enabled"] or self.power_tower.charged or self.coins < 20:
            return False
        self.coins -= 20
        self.power_tower.funding_percent += cfg["funding_step_percent"]
        if self.power_tower.funding_percent >= 100:
            self.power_tower.funding_percent = 100
            self.power_tower.charged = True
        return True

    def deploy_power_tower(self) -> bool:
        if not self.power_tower.charged or self.power_tower.active_time_remaining > 0:
            return False
        self.power_tower.charged = False
        self.power_tower.funding_percent = 0
        self.power_tower.active_time_remaining = self.config.raw["power_tower"]["duration_seconds"]
        return True

    def expected_spawn_count(self) -> int:
        enemies = self.config.raw["enemies"]
        count = enemies["base_spawn_count_per_interval"] * (1.0 + enemies["spawn_count_increase_per_level"] * (self.level - 1))
        if self.surge_time_remaining > 0:
            count *= 2
        return max(1, math.ceil(count))

    def update(self, dt: float) -> None:
        if self.loss:
            return
        self.level_timer += dt
        self.shot_counter_timer += dt
        if self.shot_counter_timer >= 1.0:
            self.shot_counter_timer = 0.0
            self.shots_fired_this_second = 0
        if self.level_timer >= self.config.raw["run"]["level_up_interval_seconds"]:
            self.level_timer -= self.config.raw["run"]["level_up_interval_seconds"]
            self.level += 1
        self.power_tower.active_time_remaining = max(0.0, self.power_tower.active_time_remaining - dt)
        self.spawn_timer -= dt
        self.surge_timer -= dt
        self.green_timer -= dt
        self.corruption_timer -= dt
        self.surge_time_remaining = max(0.0, self.surge_time_remaining - dt)
        if self.surge_timer <= 0:
            self.surge_time_remaining = 12.0
            self.surge_timer = self._roll_surge_interval()
        if self.spawn_timer <= 0:
            self.spawn_timer = self._roll_spawn_interval()
            for _ in range(self.expected_spawn_count()):
                self.enemies.append(self._spawn_enemy())
        if self.green_timer <= 0:
            self.green_timer += 2.5
            self._spread_state(LineState.GREEN)
        if self.corruption_timer <= 0:
            self.corruption_timer += self.config.raw["corruption"]["base_spread_interval_seconds"]
            self._spread_state(LineState.RED, extra_attempts=1 if self.surge_time_remaining > 0 else 0)
        self._update_towers(dt)
        self._update_orbs(dt)
        self._update_enemies(dt)
        self.loss = self.corruption_percent() >= self.config.raw["run"]["corruption_loss_threshold_percent"]

    def _spawn_enemy(self) -> Enemy:
        enemy_cfg = self.random.choice(self.config.raw["enemies"]["types"])
        edge = self.random.choice(("top", "right", "bottom", "left"))
        if edge == "top":
            x, y, dx, dy = float(self.random.randrange(self.grid_width)), 0.0, 0, 1
        elif edge == "right":
            x, y, dx, dy = float(self.max_x), float(self.random.randrange(self.grid_height)), -1, 0
        elif edge == "bottom":
            x, y, dx, dy = float(self.random.randrange(self.grid_width)), float(self.max_y), 0, -1
        else:
            x, y, dx, dy = 0.0, float(self.random.randrange(self.grid_height)), 1, 0
        return Enemy(enemy_id=enemy_cfg["id"], x=x, y=y, dx=dx, dy=dy, hp=enemy_cfg["hp"], speed=0.9 if enemy_cfg["attacks_towers"] else 0.7, attacks_towers=enemy_cfg["attacks_towers"], corruption_behavior=enemy_cfg["corruption_behavior"])

    def _update_towers(self, dt: float) -> None:
        free_actions = self.config.raw["power_tower"]["free_actions_while_active"] and self.power_tower.active_time_remaining > 0
        for hardpoint in self.hardpoints:
            tower = hardpoint.tower
            if tower is None:
                continue
            tower.cooldown = max(0.0, tower.cooldown - dt)
            if tower.cooldown > 0:
                continue
            shot_cost = tower.type_state.config["shot_cost"]
            if not free_actions and self.coins < shot_cost:
                continue
            if not free_actions:
                self.coins -= int(math.ceil(shot_cost))
            self._fire_tower(tower)
            tower.cooldown = 1.0 / max(0.05, tower.type_state.stat("fire_rate"))

    def _fire_tower(self, tower: Tower) -> None:
        cfg = tower.type_state.config
        tier = tower.type_state.grid_access_tier()
        if cfg["emission_mode"] == "spawn_at_tower":
            spawn = self._snap_to_valid_intersection(tower.hardpoint.x, tower.hardpoint.y, tier)
        else:
            spawn = self._choose_seed_target(tower)
        if spawn is None:
            return
        for _ in range(cfg.get("burst_count", 1)):
            direction = self._initial_direction(spawn[0], spawn[1], tier)
            if direction is None:
                continue
            self.shots_fired_this_second += 1
            self.orbs.append(
                Orb(
                    x=spawn[0],
                    y=spawn[1],
                    dx=direction[0],
                    dy=direction[1],
                    life_remaining=cfg["orb_lifetime_seconds"],
                    speed=self._movement_speed(cfg["path_behavior"], tower.type_state.stat("snake_speed")),
                    damage=tower.type_state.stat("hit_damage"),
                    tail_length=cfg["snake_tail_length"],
                    turn_chance=self._turn_chance(cfg["path_behavior"]),
                    access_tier=tier,
                    trail=deque([(spawn[0], spawn[1])], maxlen=cfg["snake_tail_length"]),
                )
            )

    def _movement_speed(self, path_behavior: str, stat_speed: float) -> float:
        return {"mostly_straight": 0.9, "random_walk": 0.75, "high_random_short_life": 1.05}[path_behavior] * stat_speed

    def _turn_chance(self, path_behavior: str) -> float:
        return {"mostly_straight": 0.10, "random_walk": 0.32, "high_random_short_life": 0.48}[path_behavior]

    def _choose_seed_target(self, tower: Tower) -> tuple[float, float] | None:
        prefs = tower.type_state.config["seed_targeting"]
        shot_range = tower.type_state.stat("shot_range")
        tier = tower.type_state.grid_access_tier()
        candidates = [
            segment for segment in self.all_segments()
            if self.segment_allowed_for_tier(segment.key, tier)
            and self._distance((tower.hardpoint.x, tower.hardpoint.y), segment.midpoint) <= shot_range
        ]
        if not candidates:
            return None
        preferred = LineState.RED if self.random.randint(1, 100) <= prefs["red_vs_green_percent"] else LineState.GREEN
        matches = [segment for segment in candidates if segment.state == preferred]
        if matches:
            candidates = matches
        if self.random.randint(1, 100) <= prefs["darkest_vs_random_percent"]:
            intensity = max(segment.intensity for segment in candidates)
            candidates = [segment for segment in candidates if segment.intensity == intensity]
        if self.random.randint(1, 100) <= prefs["closest_vs_random_percent"]:
            candidates.sort(key=lambda segment: self._distance((tower.hardpoint.x, tower.hardpoint.y), segment.midpoint))
            target = candidates[0]
        else:
            target = self.random.choice(candidates)
        endpoint = self._nearest_endpoint(target, tower.hardpoint.x, tower.hardpoint.y)
        return self._snap_to_valid_intersection(endpoint[0], endpoint[1], tier)

    def _nearest_endpoint(self, segment: LineSegment, ox: float, oy: float) -> tuple[float, float]:
        a, b = self.segment_endpoints(segment.key)
        return a if self._distance(a, (ox, oy)) <= self._distance(b, (ox, oy)) else b

    def _initial_direction(self, x: float, y: float, tier: str) -> tuple[int, int] | None:
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self.random.shuffle(directions)
        for dx, dy in directions:
            if self._segment_in_direction(x, y, dx, dy, tier) is not None:
                return (dx, dy)
        return None

    def _snap_to_valid_intersection(self, x: float, y: float, tier: str) -> tuple[float, float] | None:
        spacing = self.layer_spacing(tier)
        candidates: list[tuple[float, float]] = []
        for ix in range(self.grid_width):
            if ix % spacing != 0:
                continue
            for iy in range(self.grid_height):
                if iy % spacing != 0:
                    continue
                candidates.append((float(ix), float(iy)))
        candidates.sort(key=lambda point: self._distance((x, y), point))
        for candidate in candidates:
            if self._initial_direction(candidate[0], candidate[1], tier) is not None:
                return candidate
        return None

    def _update_orbs(self, dt: float) -> None:
        survivors = []
        for orb in self.orbs:
            orb.life_remaining -= dt
            if orb.life_remaining <= 0:
                continue
            distance_left = orb.speed * dt
            while distance_left > 0:
                key = self._segment_in_direction(orb.x, orb.y, orb.dx, orb.dy, orb.access_tier)
                if key is None:
                    if not self._choose_new_direction(orb):
                        break
                    continue
                to_intersection = self._distance_to_next_intersection(orb.x, orb.y, orb.dx, orb.dy)
                travel = min(distance_left, to_intersection)
                orb.x += orb.dx * travel
                orb.y += orb.dy * travel
                orb.trail.append((orb.x, orb.y))
                distance_left -= travel
                if to_intersection - travel <= 1e-6:
                    self._clean_segment(key)
                    self._damage_enemy_near(orb.x, orb.y, orb.damage)
                    self._choose_new_direction(orb)
            survivors.append(orb)
        self.orbs = [orb for orb in survivors if orb.life_remaining > 0]

    def _distance_to_next_intersection(self, x: float, y: float, dx: int, dy: int) -> float:
        if dx > 0:
            return math.ceil(x) - x if not math.isclose(x, round(x)) else 1.0
        if dx < 0:
            return x - math.floor(x) if not math.isclose(x, round(x)) else 1.0
        if dy > 0:
            return math.ceil(y) - y if not math.isclose(y, round(y)) else 1.0
        return y - math.floor(y) if not math.isclose(y, round(y)) else 1.0

    def _choose_new_direction(self, orb: Orb) -> bool:
        options = self._available_directions(orb.x, orb.y, orb.access_tier)
        if not options:
            return False
        if (orb.dx, orb.dy) in options and self.random.random() > orb.turn_chance:
            return True
        non_reverse = [direction for direction in options if direction != (-orb.dx, -orb.dy)]
        orb.dx, orb.dy = self.random.choice(non_reverse or options)
        return True

    def _available_directions(self, x: float, y: float, tier: str) -> list[tuple[int, int]]:
        if not (math.isclose(x, round(x)) and math.isclose(y, round(y))):
            return []
        result = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if self._segment_in_direction(x, y, dx, dy, tier) is not None:
                result.append((dx, dy))
        return result

    def _segment_in_direction(self, x: float, y: float, dx: int, dy: int, tier: str) -> tuple[str, int, int] | None:
        if not (math.isclose(x, round(x)) and math.isclose(y, round(y))):
            return None
        ix = int(round(x))
        iy = int(round(y))
        if dx == 1 and ix < self.max_x:
            key = ("h", ix, iy)
        elif dx == -1 and ix > 0:
            key = ("h", ix - 1, iy)
        elif dy == 1 and iy < self.max_y:
            key = ("v", ix, iy)
        elif dy == -1 and iy > 0:
            key = ("v", ix, iy - 1)
        else:
            return None
        return key if self.segment_allowed_for_tier(key, tier) else None

    def segment_allowed_for_tier(self, key: tuple[str, int, int], tier: str) -> bool:
        orientation, x, y = key
        spacing = {"large": 4, "medium": 2, "small": 1}[tier]
        fixed = y if orientation == "h" else x
        return fixed % spacing == 0

    def segment_endpoints(self, key: tuple[str, int, int]) -> tuple[tuple[float, float], tuple[float, float]]:
        orientation, x, y = key
        if orientation == "h":
            return ((float(x), float(y)), (float(x + 1), float(y)))
        return ((float(x), float(y)), (float(x), float(y + 1)))

    def _clean_segment(self, key: tuple[str, int, int]) -> None:
        segment = self.get_segment(key)
        if segment.state == LineState.BLUE:
            return
        if segment.passes_remaining <= 0:
            segment.passes_remaining = self._required_passes(segment.state, segment.intensity)
        segment.passes_remaining -= 1
        if segment.passes_remaining > 0:
            return
        if segment.state == LineState.GREEN:
            self.coins += self.config.raw["economy"]["green_harvest_income_by_intensity"][segment.intensity - 1]
        segment.state = LineState.BLUE
        segment.intensity = 0
        segment.passes_remaining = 0

    def _damage_enemy_near(self, x: float, y: float, damage: float) -> None:
        survivors = []
        for enemy in self.enemies:
            if self._distance((x, y), (enemy.x, enemy.y)) <= 0.4:
                enemy.hp -= damage
            if enemy.hp > 0:
                survivors.append(enemy)
        self.enemies = survivors

    def _update_enemies(self, dt: float) -> None:
        survivors = []
        for enemy in self.enemies:
            distance_left = enemy.speed * dt
            while distance_left > 0:
                key = self._segment_in_direction(enemy.x, enemy.y, enemy.dx, enemy.dy, "small")
                if key is None:
                    if not self._choose_enemy_direction(enemy):
                        break
                    continue
                to_intersection = self._distance_to_next_intersection(enemy.x, enemy.y, enemy.dx, enemy.dy)
                travel = min(distance_left, to_intersection)
                enemy.x += enemy.dx * travel
                enemy.y += enemy.dy * travel
                distance_left -= travel
                if to_intersection - travel <= 1e-6:
                    if self._enemy_reached_target(enemy):
                        self._enemy_arrive(enemy)
                        break
                    self._choose_enemy_direction(enemy)
            else:
                survivors.append(enemy)
                continue
            if not self._enemy_reached_target(enemy):
                survivors.append(enemy)
        self.enemies = [enemy for enemy in survivors if enemy.hp > 0]

    def _enemy_reached_target(self, enemy: Enemy) -> bool:
        tx, ty = self._enemy_target(enemy)
        return math.isclose(enemy.x, tx, abs_tol=0.01) and math.isclose(enemy.y, ty, abs_tol=0.01)

    def _choose_enemy_direction(self, enemy: Enemy) -> bool:
        options = self._available_directions(enemy.x, enemy.y, "small")
        if not options:
            return False
        tx, ty = self._enemy_target(enemy)
        reverse = (-enemy.dx, -enemy.dy)
        candidates = [direction for direction in options if direction != reverse] or options
        candidates.sort(key=lambda direction: self._enemy_direction_score(enemy, direction, tx, ty))
        enemy.dx, enemy.dy = candidates[0]
        return True

    def _enemy_direction_score(self, enemy: Enemy, direction: tuple[int, int], tx: float, ty: float) -> float:
        nx = enemy.x + direction[0]
        ny = enemy.y + direction[1]
        return abs(tx - nx) + abs(ty - ny)

    def _enemy_arrive(self, enemy: Enemy) -> None:
        key = self.closest_segment_key(enemy.x, enemy.y)
        if enemy.corruption_behavior in {"seed_drop", "both"}:
            self._increase_segment(key, LineState.RED)
        if enemy.corruption_behavior in {"spread_boost", "both"}:
            self._spread_state(LineState.RED, extra_attempts=2)
        if enemy.attacks_towers:
            tower = self._closest_tower(enemy.x, enemy.y)
            if tower:
                tower.hp -= 10
                if tower.hp <= 0:
                    tower.hardpoint.tower = None
                    tower.hardpoint.tower_type_id = None

    def _enemy_target(self, enemy: Enemy) -> tuple[float, float]:
        tower = self._closest_tower(enemy.x, enemy.y) if enemy.attacks_towers else None
        return (tower.hardpoint.x, tower.hardpoint.y) if tower else (float(round(self.max_x / 2)), float(round(self.max_y / 2)))

    def _closest_tower(self, x: float, y: float) -> Tower | None:
        towers = [hardpoint.tower for hardpoint in self.hardpoints if hardpoint.tower is not None]
        if not towers:
            return None
        return min(towers, key=lambda tower: self._distance((x, y), (tower.hardpoint.x, tower.hardpoint.y)))

    def _spread_state(self, target_state: LineState, extra_attempts: int = 0) -> None:
        profile = self.spread_profile()
        for tier in ("large", "medium", "small"):
            attempts = profile[tier] + extra_attempts
            self._spread_state_on_tier(target_state, tier, attempts)

    def _spread_state_on_tier(self, target_state: LineState, tier: str, attempts: int) -> None:
        tier_segments = [segment for segment in self.all_segments() if self.segment_allowed_for_tier(segment.key, tier)]
        matches = [segment for segment in tier_segments if segment.state == target_state]
        if not tier_segments:
            return
        if not matches:
            self._increase_segment(self.random.choice(tier_segments).key, target_state)
            return
        for _ in range(max(1, attempts)):
            origin = self.random.choice(matches)
            neighbors = [key for key in self.neighbor_segment_keys(origin.key) if self.segment_allowed_for_tier(key, tier)]
            if neighbors:
                self._increase_segment(self.random.choice(neighbors), target_state)

    def neighbor_segment_keys(self, key: tuple[str, int, int]) -> Iterable[tuple[str, int, int]]:
        seen = set()
        for endpoint in self.segment_endpoints(key):
            ix = int(round(endpoint[0]))
            iy = int(round(endpoint[1]))
            for candidate in (("h", ix, iy), ("h", ix - 1, iy), ("v", ix, iy), ("v", ix, iy - 1)):
                if candidate != key and candidate not in seen and self._segment_exists(candidate):
                    seen.add(candidate)
                    yield candidate

    def _segment_exists(self, key: tuple[str, int, int]) -> bool:
        orientation, x, y = key
        if orientation == "h":
            return 0 <= x < self.max_x and 0 <= y <= self.max_y
        return 0 <= x <= self.max_x and 0 <= y < self.max_y

    def closest_segment_key(self, x: float, y: float) -> tuple[str, int, int]:
        h_key = ("h", max(0, min(self.max_x - 1, int(math.floor(x)))), max(0, min(self.max_y, int(round(y)))))
        v_key = ("v", max(0, min(self.max_x, int(round(x)))), max(0, min(self.max_y - 1, int(math.floor(y)))))
        candidates = [key for key in (h_key, v_key) if self._segment_exists(key)]
        return min(candidates, key=lambda key: self._distance((x, y), self.get_segment(key).midpoint))

    def _increase_segment(self, key: tuple[str, int, int], target_state: LineState) -> None:
        segment = self.get_segment(key)
        if segment.state not in (LineState.BLUE, target_state):
            return
        max_intensity = self.config.raw["grid"]["intensity_levels"]
        if segment.state == LineState.BLUE:
            segment.state = target_state
            segment.intensity = 1
        else:
            segment.intensity = min(max_intensity, segment.intensity + 1)
        segment.passes_remaining = self._required_passes(target_state, segment.intensity)

    def corruption_percent(self) -> float:
        red_count = sum(1 for segment in self.all_segments() if segment.state == LineState.RED)
        return (red_count / len(self.all_segments())) * 100.0

    def _required_passes(self, state: LineState, intensity: int) -> int:
        if intensity <= 0:
            return 0
        if state == LineState.RED:
            return self.config.raw["grid"]["red_to_blue_passes_by_intensity"][intensity - 1]
        return self.config.raw["grid"]["green_to_blue_passes_by_intensity"][intensity - 1]

    def _distance(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])
