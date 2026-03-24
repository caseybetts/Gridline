from __future__ import annotations

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
class GridCell:
    state: LineState = LineState.BLUE
    intensity: int = 0
    passes_remaining: int = 0


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
    x: int
    y: int
    vx: int
    vy: int
    life_remaining: float
    speed: float
    damage: float
    tail_length: int
    turn_chance: float
    stride: int


@dataclass
class Enemy:
    enemy_id: str
    x: float
    y: float
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
        self.grid: list[list[GridCell]] = [
            [GridCell() for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        self.level = 1
        self.level_timer = 0.0
        self.spawn_timer = self._roll_spawn_interval()
        self.surge_timer = self._roll_surge_interval()
        self.surge_time_remaining = 0.0
        self.corruption_timer = config.raw["corruption"]["base_spread_interval_seconds"]
        self.green_timer = 2.5
        self.coins = config.raw["economy"]["starting_coins"]
        self.loss = False
        self.selected_tower_type_id = config.raw["towers"][0]["id"]
        self.selected_upgrade = "fire_rate"
        self.power_tower = PowerTowerState()
        self.orbs: list[Orb] = []
        self.enemies: list[Enemy] = []
        self.tower_types = {
            tower["id"]: TowerTypeState(config=tower) for tower in config.raw["towers"]
        }
        self.hardpoints = self._build_hardpoints()
        self._seed_initial_lines()

    def _seed_initial_lines(self) -> None:
        for _ in range(14):
            x = self.random.randrange(self.grid_width)
            y = self.random.randrange(self.grid_height)
            self.grid[y][x] = GridCell(LineState.GREEN, self.random.randint(1, 2))
        for _ in range(8):
            x = self.random.randrange(self.grid_width)
            y = self.random.randrange(self.grid_height)
            self.grid[y][x] = GridCell(LineState.RED, 1)

    def _build_hardpoints(self) -> list[Hardpoint]:
        count = self.config.raw["tower_placement"]["hardpoint_count"]
        activation_costs = self.config.raw["tower_placement"]["activation_cost_by_slot"]
        points: list[tuple[float, float]] = []
        for index in range(count):
            t = index / count
            perimeter = t * 4
            if perimeter < 1:
                points.append((perimeter, 0))
            elif perimeter < 2:
                points.append((1, perimeter - 1))
            elif perimeter < 3:
                points.append((3 - perimeter, 1))
            else:
                points.append((0, 4 - perimeter))
        return [
            Hardpoint(
                index=index,
                x=px * (self.grid_width - 1),
                y=py * (self.grid_height - 1),
                activation_cost=activation_costs[index],
            )
            for index, (px, py) in enumerate(points)
        ]

    def _roll_spawn_interval(self) -> float:
        enemies = self.config.raw["enemies"]
        return self.random.uniform(
            enemies["random_spawn_interval_min_seconds"],
            enemies["random_spawn_interval_max_seconds"],
        )

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
        cost = hardpoint.activation_cost + tower_cfg["build_cost"]
        if self.coins < cost:
            return False
        self.coins -= cost
        tower = Tower(type_state=self.tower_types[tower_type_id], hardpoint=hardpoint)
        hardpoint.tower_type_id = tower_type_id
        hardpoint.tower = tower
        return True

    def upgrade_selected_tower_type(self, upgrade_key: str | None = None) -> bool:
        upgrade_key = upgrade_key or self.selected_upgrade
        state = self.tower_types[self.selected_tower_type_id]
        cost_curve = self.config.raw["upgrades"]["cost_curve_multiplier"]
        cost = state.upgrade_cost(upgrade_key, cost_curve)
        if self.coins < cost:
            return False
        self.coins -= cost
        state.upgrade_levels[upgrade_key] += 1
        for hardpoint in self.hardpoints:
            if hardpoint.tower and hardpoint.tower.type_state is state and upgrade_key == "hp":
                hardpoint.tower.hp = state.stat("hp")
        return True

    def fund_power_tower(self) -> bool:
        cfg = self.config.raw["power_tower"]
        if not cfg["enabled"] or self.power_tower.charged:
            return False
        step_cost = 20
        if self.coins < step_cost:
            return False
        self.coins -= step_cost
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
        count = enemies["base_spawn_count_per_interval"] * (
            1.0 + enemies["spawn_count_increase_per_level"] * (self.level - 1)
        )
        if self.surge_time_remaining > 0:
            count *= 2.0
        return max(1, math.ceil(count))

    def update(self, dt: float) -> None:
        if self.loss:
            return
        self.level_timer += dt
        if self.level_timer >= self.config.raw["run"]["level_up_interval_seconds"]:
            self.level_timer -= self.config.raw["run"]["level_up_interval_seconds"]
            self.level += 1

        self.power_tower.active_time_remaining = max(0.0, self.power_tower.active_time_remaining - dt)
        self.spawn_timer -= dt
        self.surge_timer -= dt
        self.corruption_timer -= dt
        self.green_timer -= dt
        self.surge_time_remaining = max(0.0, self.surge_time_remaining - dt)

        if self.surge_timer <= 0:
            self.surge_time_remaining = 12.0
            self.surge_timer = self._roll_surge_interval()

        if self.spawn_timer <= 0:
            self.spawn_timer = self._roll_spawn_interval()
            for _ in range(self.expected_spawn_count()):
                self.enemies.append(self._spawn_enemy())

        if self.corruption_timer <= 0:
            self.corruption_timer += self.config.raw["corruption"]["base_spread_interval_seconds"]
            self._spread_red()

        if self.green_timer <= 0:
            self.green_timer += 2.5
            self._spread_green()

        self._update_towers(dt)
        self._update_orbs(dt)
        self._update_enemies(dt)
        self.loss = self.corruption_percent() >= self.config.raw["run"]["corruption_loss_threshold_percent"]

    def _spawn_enemy(self) -> Enemy:
        enemy_cfg = self.random.choice(self.config.raw["enemies"]["types"])
        edge = self.random.choice(("top", "right", "bottom", "left"))
        if edge == "top":
            x, y = self.random.uniform(0, self.grid_width - 1), 0.0
        elif edge == "right":
            x, y = self.grid_width - 1.0, self.random.uniform(0, self.grid_height - 1)
        elif edge == "bottom":
            x, y = self.random.uniform(0, self.grid_width - 1), self.grid_height - 1.0
        else:
            x, y = 0.0, self.random.uniform(0, self.grid_height - 1)

        return Enemy(
            enemy_id=enemy_cfg["id"],
            x=x,
            y=y,
            hp=enemy_cfg["hp"],
            speed=1.8 if enemy_cfg["attacks_towers"] else 1.4,
            attacks_towers=enemy_cfg["attacks_towers"],
            corruption_behavior=enemy_cfg["corruption_behavior"],
        )

    def _update_towers(self, dt: float) -> None:
        for hardpoint in self.hardpoints:
            tower = hardpoint.tower
            if tower is None:
                continue
            tower.cooldown = max(0.0, tower.cooldown - dt)
            if tower.cooldown > 0:
                continue
            shot_cost = tower.type_state.config["shot_cost"]
            free_actions = self.config.raw["power_tower"]["free_actions_while_active"] and self.power_tower.active_time_remaining > 0
            if not free_actions and self.coins < shot_cost:
                continue
            if not free_actions:
                self.coins -= int(math.ceil(shot_cost))
            self._fire_tower(tower)
            fire_rate = tower.type_state.stat("fire_rate")
            tower.cooldown = 1.0 / max(0.05, fire_rate)

    def _fire_tower(self, tower: Tower) -> None:
        cfg = tower.type_state.config
        count = cfg.get("burst_count", 1)
        if cfg["emission_mode"] == "projectile_seed":
            spawn_x, spawn_y = self._choose_seed_target(cfg, tower)
        else:
            spawn_x = int(round(tower.hardpoint.x))
            spawn_y = int(round(tower.hardpoint.y))

        for _ in range(count):
            direction = self.random.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            path_behavior = cfg["path_behavior"]
            turn_chance = {
                "mostly_straight": 0.08,
                "random_walk": 0.2,
                "high_random_short_life": 0.35,
            }[path_behavior]
            stride = {
                "large": 4,
                "medium": 2,
                "small": 1,
            }[tower.type_state.grid_access_tier()]
            self.orbs.append(
                Orb(
                    x=spawn_x,
                    y=spawn_y,
                    vx=direction[0],
                    vy=direction[1],
                    life_remaining=cfg["orb_lifetime_seconds"],
                    speed=tower.type_state.stat("snake_speed"),
                    damage=tower.type_state.stat("hit_damage"),
                    tail_length=cfg["snake_tail_length"],
                    turn_chance=turn_chance,
                    stride=stride,
                )
            )

    def _choose_seed_target(self, tower_cfg: dict, tower: Tower) -> tuple[int, int]:
        prefs = tower_cfg["seed_targeting"]
        cells = [(x, y, cell) for y, row in enumerate(self.grid) for x, cell in enumerate(row)]
        preferred_state = LineState.RED if self.random.randint(1, 100) <= prefs["red_vs_green_percent"] else LineState.GREEN
        matching = [item for item in cells if item[2].state == preferred_state]
        if not matching:
            matching = cells
        if self.random.randint(1, 100) <= prefs["darkest_vs_random_percent"]:
            max_intensity = max(item[2].intensity for item in matching)
            matching = [item for item in matching if item[2].intensity == max_intensity]
        if self.random.randint(1, 100) <= prefs["closest_vs_random_percent"]:
            ox = tower.hardpoint.x
            oy = tower.hardpoint.y
            matching.sort(key=lambda item: abs(item[0] - ox) + abs(item[1] - oy))
            x, y, _ = matching[0]
            return x, y
        x, y, _ = self.random.choice(matching)
        return x, y

    def _update_orbs(self, dt: float) -> None:
        survivors: list[Orb] = []
        for orb in self.orbs:
            orb.life_remaining -= dt
            if orb.life_remaining <= 0:
                continue
            steps = max(1, int(math.ceil(orb.speed * dt * 6)))
            for _ in range(steps):
                self._maybe_turn_orb(orb)
                orb.x = min(self.grid_width - 1, max(0, orb.x + orb.vx * orb.stride))
                orb.y = min(self.grid_height - 1, max(0, orb.y + orb.vy * orb.stride))
                self._clean_cell(orb.x, orb.y)
                self._damage_enemy_at(orb.x, orb.y, orb.damage)
            survivors.append(orb)
        self.orbs = survivors

    def _maybe_turn_orb(self, orb: Orb) -> None:
        if self.random.random() > orb.turn_chance:
            return
        if orb.vx != 0:
            orb.vx, orb.vy = 0, self.random.choice((-1, 1))
        else:
            orb.vx, orb.vy = self.random.choice((-1, 1)), 0

    def _clean_cell(self, x: int, y: int) -> None:
        cell = self.grid[y][x]
        if cell.state == LineState.BLUE:
            return
        if cell.passes_remaining <= 0:
            cell.passes_remaining = self._required_passes(cell.state, cell.intensity)
        cell.passes_remaining -= 1
        if cell.passes_remaining > 0:
            return
        if cell.state == LineState.GREEN:
            income = self.config.raw["economy"]["green_harvest_income_by_intensity"][cell.intensity - 1]
            self.coins += income
            self.grid[y][x] = GridCell(LineState.BLUE, 0, 0)
            return
        self.grid[y][x] = GridCell(LineState.BLUE, 0, 0)

    def _damage_enemy_at(self, x: int, y: int, damage: float) -> None:
        for enemy in self.enemies:
            if int(round(enemy.x)) == x and int(round(enemy.y)) == y:
                enemy.hp -= damage
        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]

    def _update_enemies(self, dt: float) -> None:
        survivors: list[Enemy] = []
        for enemy in self.enemies:
            target_x, target_y = self._enemy_target(enemy)
            dx = target_x - enemy.x
            dy = target_y - enemy.y
            distance = max(0.0001, math.hypot(dx, dy))
            enemy.x += dx / distance * enemy.speed * dt
            enemy.y += dy / distance * enemy.speed * dt

            if distance < 0.55:
                gx = min(self.grid_width - 1, max(0, int(round(enemy.x))))
                gy = min(self.grid_height - 1, max(0, int(round(enemy.y))))
                if enemy.corruption_behavior in {"seed_drop", "both"}:
                    self._increase_cell(gx, gy, LineState.RED)
                if enemy.corruption_behavior in {"spread_boost", "both"}:
                    self._spread_red(extra_attempts=2)
                if enemy.attacks_towers:
                    tower = self._closest_tower(enemy.x, enemy.y)
                    if tower:
                        tower.hp -= 10
                        if tower.hp <= 0:
                            tower.hardpoint.tower = None
                            tower.hardpoint.tower_type_id = None
                continue
            survivors.append(enemy)
        self.enemies = [enemy for enemy in survivors if enemy.hp > 0]

    def _enemy_target(self, enemy: Enemy) -> tuple[float, float]:
        tower = self._closest_tower(enemy.x, enemy.y) if enemy.attacks_towers else None
        if tower:
            return tower.hardpoint.x, tower.hardpoint.y
        return (self.grid_width - 1) / 2, (self.grid_height - 1) / 2

    def _closest_tower(self, x: float, y: float) -> Tower | None:
        living = [hardpoint.tower for hardpoint in self.hardpoints if hardpoint.tower is not None]
        if not living:
            return None
        return min(living, key=lambda tower: (tower.hardpoint.x - x) ** 2 + (tower.hardpoint.y - y) ** 2)

    def _spread_red(self, extra_attempts: int = 0) -> None:
        attempts = 2 + extra_attempts
        red_cells = [(x, y) for y, row in enumerate(self.grid) for x, cell in enumerate(row) if cell.state == LineState.RED]
        if not red_cells:
            x = self.random.randrange(self.grid_width)
            y = self.random.randrange(self.grid_height)
            self._increase_cell(x, y, LineState.RED)
            return
        for _ in range(attempts):
            x, y = self.random.choice(red_cells)
            nx, ny = self.random.choice(list(self._neighbors(x, y)))
            self._increase_cell(nx, ny, LineState.RED)

    def _spread_green(self) -> None:
        green_cells = [(x, y) for y, row in enumerate(self.grid) for x, cell in enumerate(row) if cell.state == LineState.GREEN]
        if not green_cells:
            x = self.random.randrange(self.grid_width)
            y = self.random.randrange(self.grid_height)
            self._increase_cell(x, y, LineState.GREEN)
            return
        x, y = self.random.choice(green_cells)
        nx, ny = self.random.choice(list(self._neighbors(x, y)))
        self._increase_cell(nx, ny, LineState.GREEN)

    def _increase_cell(self, x: int, y: int, target_state: LineState) -> None:
        cell = self.grid[y][x]
        max_intensity = self.config.raw["grid"]["intensity_levels"]
        if cell.state not in (LineState.BLUE, target_state):
            return
        if cell.state == LineState.BLUE:
            self.grid[y][x] = GridCell(target_state, 1, self._required_passes(target_state, 1))
        else:
            cell.intensity = min(max_intensity, cell.intensity + 1)
            cell.passes_remaining = self._required_passes(target_state, cell.intensity)

    def _neighbors(self, x: int, y: int) -> Iterable[tuple[int, int]]:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                yield nx, ny

    def corruption_percent(self) -> float:
        total = self.grid_width * self.grid_height
        red = sum(1 for row in self.grid for cell in row if cell.state == LineState.RED)
        return (red / total) * 100.0

    def _required_passes(self, state: LineState, intensity: int) -> int:
        if intensity <= 0:
            return 0
        if state == LineState.RED:
            return self.config.raw["grid"]["red_to_blue_passes_by_intensity"][intensity - 1]
        if state == LineState.GREEN:
            return self.config.raw["grid"]["green_to_blue_passes_by_intensity"][intensity - 1]
        return 0
