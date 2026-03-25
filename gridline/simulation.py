from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import math
import random

from .spec import GameSpec, TIER_INDEX
from .topology import Hardpoint, Topology, allowed_tiers, build_topology


@dataclass
class SegmentState:
    color: str = "blue"
    intensity: int = 0
    clean_progress: float = 0.0
    harvest_progress: float = 0.0


@dataclass
class TowerInstance:
    key: str
    hardpoint_id: str
    archetype: str
    hp: float
    max_hp: float
    active_mode: str = "default"
    secondary_unlocked: bool = False
    fire_cooldown: float = 0.0
    swap_cooldown: float = 0.0
    seed_closest_vs_random: int = 70
    seed_red_vs_green: int = 70
    seed_darkest_vs_random: int = 60


@dataclass
class HardpointState:
    hardpoint: Hardpoint
    tower: TowerInstance | None = None


@dataclass
class Orb:
    key: str
    owner_tower_id: str
    owner_hardpoint_id: str
    segment_id: str
    from_node: str
    to_node: str
    distance_on_segment: float
    lifetime_remaining: float
    speed: float
    damage: float
    clean_rate: float
    harvest_rate: float
    turn_chance: float
    current_tier: str
    mode: str
    home_node_id: str
    previous_node: str | None = None
    trail_nodes: list[str] = field(default_factory=list)
    forced_uturn_used: bool = False
    burst_bias_forward: float | None = None


@dataclass
class SeedFlight:
    key: str
    owner_tower_id: str
    owner_hardpoint_id: str
    start_node_id: str
    target_node_id: str
    mode: str
    current_tier: str
    time_remaining: float
    total_time: float
    speed: float
    damage: float
    clean_rate: float
    harvest_rate: float
    turn_chance: float


@dataclass
class Enemy:
    key: str
    enemy_type: str
    hp: float
    segment_id: str
    from_node: str
    to_node: str
    distance_on_segment: float
    speed: float
    initial_path_budget: int = 0
    target_hardpoint_id: str | None = None
    fallback_target_segment_id: str | None = None
    path_budget_remaining: int = 0


@dataclass
class PowerState:
    funding_percent: int = 0
    charged: bool = False
    active_hardpoint_id: str | None = None
    time_remaining: float = 0.0
    hp: float = 0.0
    suspended_tower: TowerInstance | None = None
    fire_cooldown: float = 0.0


@dataclass
class SegmentImpact:
    color: str
    intensity: int
    time_remaining: float
    duration: float


@dataclass
class SeedPulse:
    node_id: str
    time_remaining: float
    duration: float


UPGRADE_DISPLAY = {
    "fire_rate": "Fire Rate",
    "hp": "HP",
    "snake_speed": "Snake Speed",
    "hit_damage": "Damage",
    "shot_range": "Shot Range",
    "grid_access_tier": "Grid Tier",
}


class GameSimulation:
    def __init__(self, spec: GameSpec, seed: int = 7) -> None:
        self.spec = spec
        self.random = random.Random(seed)
        self.topology: Topology = build_topology(spec)
        self.segment_states = {
            segment_id: SegmentState()
            for segment_id in self.topology.segments
        }
        self.hardpoints = {
            hardpoint.key: HardpointState(hardpoint=hardpoint)
            for hardpoint in self.topology.hardpoints
        }
        self.towers: dict[str, TowerInstance] = {}
        self.orbs: dict[str, Orb] = {}
        self.seed_flights: dict[str, SeedFlight] = {}
        self.enemies: dict[str, Enemy] = {}
        self.power = PowerState()
        self.segment_impacts: dict[str, SegmentImpact] = {}
        self.seed_pulses: list[SeedPulse] = []
        self.global_upgrade_levels = {
            tower_key: {name: 0 for name in self.spec.upgrade_costs}
            for tower_key in self.spec.towers
        }
        self.selected_hardpoint_id: str | None = None
        self.coins = spec.starting_coins
        self.run_time = 0.0
        self.level = 1
        self.game_over = False
        self.shots_fired_times: deque[float] = deque()
        self.spawn_timer = spec.base_spawn_interval
        self.spread_timer = spec.spread_interval
        self.green_spread_timer = spec.green_spread_interval
        self.level_timer = spec.level_interval
        self.surge_roll_timer = spec.surge_roll_interval
        self.surge_time_remaining = 0.0
        self._id_counter = 0
        self._seed_initial_line_states()

    def _seed_initial_line_states(self) -> None:
        segments = list(self.topology.segments.keys())
        center = self.topology.center
        center_sorted = sorted(
            segments,
            key=lambda item: math.dist(self.topology.segment_midpoint(item), center),
        )
        edge_sorted = sorted(
            segments,
            key=lambda item: -math.dist(self.topology.segment_midpoint(item), center),
        )
        for segment_id in center_sorted[:6]:
            self.segment_states[segment_id].color = "red"
            self.segment_states[segment_id].intensity = 1
        for segment_id in edge_sorted[:8]:
            self.segment_states[segment_id].color = "green"
            self.segment_states[segment_id].intensity = 1

    def next_id(self, prefix: str) -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def selected_hardpoint(self) -> HardpointState | None:
        if self.selected_hardpoint_id is None:
            return None
        return self.hardpoints.get(self.selected_hardpoint_id)

    def click_world(self, x: float, y: float) -> None:
        nearest: tuple[float, str] | None = None
        for hardpoint_id, hardpoint_state in self.hardpoints.items():
            node = self.topology.nodes[hardpoint_state.hardpoint.node_id]
            distance = math.dist((x, y), (node.x, node.y))
            if distance <= self.spec.visuals.hardpoint_radius * 2.2:
                if nearest is None or distance < nearest[0]:
                    nearest = (distance, hardpoint_id)
        self.selected_hardpoint_id = nearest[1] if nearest else None

    def build_tower(self, tower_key: str) -> bool:
        hardpoint_state = self.selected_hardpoint()
        tower_spec = self.spec.towers[tower_key]
        if (
            hardpoint_state is None
            or hardpoint_state.tower is not None
            or self.game_over
        ):
            return False
        if self.coins < tower_spec.build_cost:
            return False
        self.coins -= tower_spec.build_cost
        tower = TowerInstance(
            key=self.next_id("tower"),
            hardpoint_id=hardpoint_state.hardpoint.key,
            archetype=tower_key,
            hp=self.tower_hp_value(tower_key),
            max_hp=self.tower_hp_value(tower_key),
            seed_closest_vs_random=self.spec.seed_closest_default,
            seed_red_vs_green=self.spec.seed_red_green_default,
            seed_darkest_vs_random=self.spec.seed_darkest_default,
        )
        hardpoint_state.tower = tower
        self.towers[tower.key] = tower
        return True

    def purchase_secondary_mode(self) -> bool:
        tower = self.selected_action_tower()
        if tower is None or tower.secondary_unlocked:
            return False
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if mode_spec is None or self.coins < mode_spec.purchase_cost:
            return False
        self.coins -= mode_spec.purchase_cost
        tower.secondary_unlocked = True
        return True

    def toggle_selected_mode(self) -> bool:
        tower = self.selected_action_tower()
        if tower is None or not tower.secondary_unlocked or tower.swap_cooldown > 0:
            return False
        tower.active_mode = "secondary" if tower.active_mode == "default" else "default"
        tower.swap_cooldown = self.spec.behavior_swap_cooldown
        return True

    def adjust_seed_lever(self, lever: str, delta: int) -> None:
        tower = self.selected_action_tower()
        if tower is None or tower.archetype != "seed_tower":
            return
        attr = {
            "closest": "seed_closest_vs_random",
            "color": "seed_red_vs_green",
            "darkest": "seed_darkest_vs_random",
        }[lever]
        value = max(0, min(100, getattr(tower, attr) + delta))
        setattr(tower, attr, int(round(value / 5.0) * 5))

    def upgrade_selected_tower_type(self, stat_name: str) -> bool:
        tower = self.selected_action_tower()
        if tower is None:
            return False
        levels = self.global_upgrade_levels[tower.archetype]
        current_level = levels[stat_name]
        costs = self.spec.upgrade_costs[stat_name]
        if current_level >= len(costs):
            return False
        cost = costs[current_level]
        if self.coins < cost:
            return False
        self.coins -= cost
        levels[stat_name] += 1
        if stat_name == "hp":
            for existing in self.towers.values():
                if existing.archetype != tower.archetype:
                    continue
                old_max = existing.max_hp
                new_max = self.tower_hp_value(existing.archetype)
                ratio = existing.hp / old_max if old_max > 0 else 1.0
                existing.max_hp = new_max
                existing.hp = min(new_max, new_max * ratio)
        return True

    def fund_power(self) -> bool:
        if (
            self.power.active_hardpoint_id is not None
            or self.power.charged
            or self.power.funding_percent >= 100
            or self.coins < self.spec.power_funding_chunk_cost
        ):
            return False
        self.coins -= self.spec.power_funding_chunk_cost
        self.power.funding_percent += 10
        if self.power.funding_percent >= 100:
            self.power.funding_percent = 100
            self.power.charged = True
        return True

    def deploy_power_to_selected(self) -> bool:
        hardpoint_state = self.selected_hardpoint()
        if hardpoint_state is None or not self.power.charged or self.power.active_hardpoint_id is not None:
            return False
        self.power.active_hardpoint_id = hardpoint_state.hardpoint.key
        self.power.time_remaining = self.spec.power_duration
        self.power.hp = self.spec.power_hp
        self.power.fire_cooldown = 0.0
        self.power.charged = False
        self.power.funding_percent = 0
        self.power.suspended_tower = hardpoint_state.tower
        return True

    def current_tower(self) -> TowerInstance | None:
        hardpoint_state = self.selected_hardpoint()
        if hardpoint_state is None:
            return None
        if self.power.active_hardpoint_id == hardpoint_state.hardpoint.key:
            return self.power.suspended_tower
        return hardpoint_state.tower

    def selected_power_active(self) -> bool:
        hardpoint_state = self.selected_hardpoint()
        return bool(
            hardpoint_state is not None
            and self.power.active_hardpoint_id == hardpoint_state.hardpoint.key
        )

    def selected_action_tower(self) -> TowerInstance | None:
        if self.selected_power_active():
            return None
        return self.current_tower()

    def selected_object_snapshot(self) -> dict[str, object]:
        hardpoint_state = self.selected_hardpoint()
        if hardpoint_state is None:
            return {"kind": "none"}
        if self.selected_power_active():
            return {
                "kind": "power",
                "name": "Power Tower",
                "hp": self.power.hp,
                "max_hp": self.spec.power_hp,
                "mode": "power",
                "fire_ready": self.power.fire_cooldown <= 0,
                "fire_cooldown": self.power.fire_cooldown,
                "time_remaining": self.power.time_remaining,
                "underlying_tower_name": (
                    self.spec.towers[hardpoint_state.tower.archetype].name
                    if hardpoint_state.tower is not None
                    else None
                ),
            }
        tower = hardpoint_state.tower
        if tower is None:
            return {"kind": "empty"}
        return {
            "kind": "tower",
            "name": self.spec.towers[tower.archetype].name,
            "hp": tower.hp,
            "max_hp": tower.max_hp,
            "mode": tower.active_mode,
            "fire_ready": tower.fire_cooldown <= 0,
            "fire_cooldown": tower.fire_cooldown,
            "swap_cooldown": tower.swap_cooldown,
            "secondary_unlocked": tower.secondary_unlocked,
            "tower": tower,
        }

    def update(self, dt: float) -> None:
        if self.game_over:
            return
        self.run_time += dt
        self.level_timer -= dt
        self.surge_roll_timer -= dt
        if self.level_timer <= 0:
            self.level += 1
            self.level_timer += self.spec.level_interval
        if self.surge_roll_timer <= 0:
            self.surge_roll_timer += self.spec.surge_roll_interval
            if self.random.random() < 0.35 and self.surge_time_remaining <= 0:
                self.surge_time_remaining = self.spec.surge_duration
        if self.surge_time_remaining > 0:
            self.surge_time_remaining = max(0.0, self.surge_time_remaining - dt)
        self._update_towers(dt)
        self._update_seed_flights(dt)
        self._update_orbs(dt)
        self._update_enemies(dt)
        self._update_power(dt)
        self._update_spread(dt)
        self._update_feedback_effects(dt)
        self._spawn_enemies(dt)
        self._trim_shot_history()
        if self.corruption_percent() >= self.spec.corruption_failure_threshold:
            self.game_over = True

    def _update_towers(self, dt: float) -> None:
        for tower in list(self.towers.values()):
            if tower.hp <= 0:
                self._destroy_tower(tower)
                continue
            tower.fire_cooldown = max(0.0, tower.fire_cooldown - dt)
            tower.swap_cooldown = max(0.0, tower.swap_cooldown - dt)
            if self.power.active_hardpoint_id == tower.hardpoint_id:
                continue
            if tower.fire_cooldown <= 0:
                self._attempt_fire_tower(tower)
        if self.power.active_hardpoint_id is not None and self.power.time_remaining > 0:
            self.power.fire_cooldown = max(0.0, self.power.fire_cooldown - dt)
            if self.power.fire_cooldown <= 0:
                self._attempt_fire_power()

    def _attempt_fire_power(self) -> None:
        hardpoint_id = self.power.active_hardpoint_id
        if hardpoint_id is None:
            return
        hardpoint_state = self.hardpoints[hardpoint_id]
        launch_node = self.topology.nodes[hardpoint_state.hardpoint.node_id]
        segment_id, to_node = self._pick_initial_segment(launch_node.key, "small")
        if segment_id is None:
            return
        orb_key = self.next_id("orb")
        self.orbs[orb_key] = Orb(
            key=orb_key,
            owner_tower_id="power_tower",
            owner_hardpoint_id=hardpoint_id,
            segment_id=segment_id,
            from_node=launch_node.key,
            to_node=to_node,
            distance_on_segment=0.0,
            lifetime_remaining=self.spec.power_lifetime,
            speed=self.spec.power_snake_speed,
            damage=self.spec.power_hit_damage,
            clean_rate=self.spec.power_clean_per_unit_distance,
            harvest_rate=self.spec.power_harvest_per_unit_distance,
            turn_chance=self.spec.power_turn_chance,
            current_tier=self.spec.power_grid_access_tier,
            mode="power",
            home_node_id=launch_node.key,
        )
        self.power.fire_cooldown = 1.0 / self.spec.power_fire_rate
        self.shots_fired_times.append(self.run_time)

    def _attempt_fire_tower(self, tower: TowerInstance) -> None:
        tower_spec = self.spec.towers[tower.archetype]
        mode_spec = tower_spec.secondary_mode if tower.active_mode == "secondary" else None
        shot_cost = tower_spec.shot_cost * (mode_spec.shot_cost_multiplier if mode_spec else 1.0)
        if self.coins < shot_cost:
            return
        self.coins -= shot_cost
        tower.fire_cooldown = 1.0 / (self.fire_rate_value(tower) * (mode_spec.fire_rate_multiplier if mode_spec else 1.0))
        burst_count = mode_spec.burst_count_override if (mode_spec and mode_spec.burst_count_override) else tower_spec.burst_count
        hardpoint_state = self.hardpoints[tower.hardpoint_id]
        launch_node = self.topology.nodes[hardpoint_state.hardpoint.node_id]
        for _ in range(burst_count):
            if tower.archetype == "seed_tower" and tower.active_mode == "default":
                target_node_id = self._select_seed_target(tower, launch_node.key, self.shot_range_value(tower))
                if target_node_id is None:
                    continue
                self._launch_seed_flight(tower, launch_node.key, target_node_id)
                continue
            elif tower.archetype == "seed_tower" and mode_spec and mode_spec.launch_range_override:
                local_target = self._select_local_node(launch_node.key, self.shot_range_value(tower, mode_spec.launch_range_override))
                if local_target is None:
                    continue
                self._launch_seed_flight(tower, launch_node.key, local_target)
                continue
            self._spawn_orb_from_node(tower, launch_node.key, launch_node.key)
        self.shots_fired_times.append(self.run_time)

    def _launch_seed_flight(self, tower: TowerInstance, start_node_id: str, target_node_id: str) -> None:
        start_node = self.topology.nodes[start_node_id]
        target_node = self.topology.nodes[target_node_id]
        speed = max(220.0, self.snake_speed_value(tower) * 3.0)
        travel_time = max(0.10, math.dist((start_node.x, start_node.y), (target_node.x, target_node.y)) / speed)
        flight = SeedFlight(
            key=self.next_id("seed"),
            owner_tower_id=tower.key,
            owner_hardpoint_id=tower.hardpoint_id,
            start_node_id=start_node_id,
            target_node_id=target_node_id,
            mode=tower.active_mode,
            current_tier=self.tower_grid_access_tier(tower),
            time_remaining=travel_time,
            total_time=travel_time,
            speed=self.snake_speed_value(tower) * self.speed_multiplier(tower),
            damage=self.hit_damage_value(tower) * self.damage_multiplier(tower),
            clean_rate=self.spec.towers[tower.archetype].clean_per_unit_distance * self.clean_multiplier(tower),
            harvest_rate=self.spec.towers[tower.archetype].harvest_per_unit_distance * self.harvest_multiplier(tower),
            turn_chance=self.turn_chance(tower),
        )
        self.seed_flights[flight.key] = flight

    def _spawn_orb_from_node(self, tower: TowerInstance, start_node_id: str, home_node_id: str) -> bool:
        tower_spec = self.spec.towers[tower.archetype]
        mode_spec = tower_spec.secondary_mode if tower.active_mode == "secondary" else None
        segment_id, to_node = self._pick_initial_segment(start_node_id, self.tower_grid_access_tier(tower))
        if segment_id is None:
            return False
        orb = Orb(
            key=self.next_id("orb"),
            owner_tower_id=tower.key,
            owner_hardpoint_id=tower.hardpoint_id,
            segment_id=segment_id,
            from_node=start_node_id,
            to_node=to_node,
            distance_on_segment=0.0,
            lifetime_remaining=tower_spec.lifetime,
            speed=self.snake_speed_value(tower) * self.speed_multiplier(tower),
            damage=self.hit_damage_value(tower) * self.damage_multiplier(tower),
            clean_rate=tower_spec.clean_per_unit_distance * self.clean_multiplier(tower),
            harvest_rate=tower_spec.harvest_per_unit_distance * self.harvest_multiplier(tower),
            turn_chance=self.turn_chance(tower),
            current_tier=self.tower_grid_access_tier(tower),
            mode=tower.active_mode,
            home_node_id=home_node_id,
            burst_bias_forward=tower_spec.secondary_mode.forward_bias if (mode_spec and tower.active_mode == "secondary") else None,
        )
        self.orbs[orb.key] = orb
        return True

    def _update_seed_flights(self, dt: float) -> None:
        for flight in list(self.seed_flights.values()):
            flight.time_remaining -= dt
            if flight.time_remaining > 0:
                continue
            tower = self.towers.get(flight.owner_tower_id)
            self.seed_flights.pop(flight.key, None)
            if tower is None:
                continue
            self._spawn_orb_from_node(tower, flight.target_node_id, self.topology.nodes[self.hardpoints[tower.hardpoint_id].hardpoint.node_id].key)

    def _pick_initial_segment(self, node_id: str, max_tier: str) -> tuple[str | None, str | None]:
        candidates = self._legal_segments_from_node(node_id, None, max_tier)
        if not candidates:
            return None, None
        segment_id = self.random.choice(candidates)
        segment = self.topology.segments[segment_id]
        next_node = segment.b if segment.a == node_id else segment.a
        return segment_id, next_node

    def _select_local_node(self, home_node_id: str, radius: float) -> str | None:
        home = self.topology.nodes[home_node_id]
        candidates = [
            node.key
            for node in self.topology.nodes.values()
            if {"large", "medium", "small"} & node.tiers
            and math.dist((home.x, home.y), (node.x, node.y)) <= radius
        ]
        return self.random.choice(candidates) if candidates else None

    def _select_seed_target(self, tower: TowerInstance, home_node_id: str, shot_range: float) -> str | None:
        home = self.topology.nodes[home_node_id]
        candidates = [
            node
            for node in self.topology.nodes.values()
            if {"large", "medium"} & node.tiers
            and math.dist((home.x, home.y), (node.x, node.y)) <= shot_range
        ]
        if not candidates:
            return None
        bucket = candidates
        wants_red = self.random.random() < (tower.seed_red_vs_green / 100.0)
        preferred_color = "red" if wants_red else "green"
        preferred = [node for node in bucket if self._node_color_bucket(node.key) == preferred_color]
        alternate = [node for node in bucket if self._node_color_bucket(node.key) in {"red", "green"} and node not in preferred]
        if preferred:
            bucket = preferred
        elif alternate:
            bucket = alternate
        if self.random.random() < (tower.seed_closest_vs_random / 100.0):
            min_distance = min(math.dist((home.x, home.y), (node.x, node.y)) for node in bucket)
            bucket = [
                node
                for node in bucket
                if math.isclose(math.dist((home.x, home.y), (node.x, node.y)), min_distance, rel_tol=1e-5)
            ] or bucket
        if self.random.random() < (tower.seed_darkest_vs_random / 100.0):
            highest = max(self._node_intensity(node.key) for node in bucket)
            bucket = [node for node in bucket if self._node_intensity(node.key) == highest] or bucket
        return self.random.choice(bucket).key if bucket else None

    def _node_color_bucket(self, node_id: str) -> str:
        color = "blue"
        strongest = -1
        for segment_id in self.topology.nodes[node_id].segment_ids:
            state = self.segment_states[segment_id]
            if state.color != "blue" and state.intensity > strongest:
                strongest = state.intensity
                color = state.color
        return color

    def _node_intensity(self, node_id: str) -> int:
        return max((self.segment_states[segment_id].intensity for segment_id in self.topology.nodes[node_id].segment_ids), default=0)

    def _update_orbs(self, dt: float) -> None:
        for orb in list(self.orbs.values()):
            orb.lifetime_remaining -= dt
            if orb.lifetime_remaining <= 0:
                self.orbs.pop(orb.key, None)
                continue
            segment = self.topology.segments[orb.segment_id]
            travel = orb.speed * dt
            self._apply_orb_to_segment(orb.segment_id, travel, orb)
            orb.distance_on_segment += travel
            while orb.distance_on_segment >= segment.length:
                overflow = orb.distance_on_segment - segment.length
                current_node = orb.to_node
                next_segment_id, next_node = self._choose_next_segment(orb, current_node)
                if next_segment_id is None:
                    self.orbs.pop(orb.key, None)
                    break
                orb.trail_nodes.insert(0, orb.from_node)
                if len(orb.trail_nodes) > 16:
                    orb.trail_nodes.pop()
                orb.previous_node = orb.from_node
                orb.from_node = current_node
                orb.to_node = next_node
                orb.segment_id = next_segment_id
                orb.distance_on_segment = overflow
                segment = self.topology.segments[orb.segment_id]
            if orb.key in self.orbs:
                self._damage_enemies_on_segment(orb)

    def _apply_orb_to_segment(self, segment_id: str, distance: float, orb: Orb) -> None:
        state = self.segment_states[segment_id]
        if state.color == "red" and state.intensity > 0:
            state.clean_progress += distance * orb.clean_rate
            threshold = self.spec.red_clean_thresholds[state.intensity - 1]
            while state.intensity > 0 and state.clean_progress >= threshold:
                state.clean_progress -= threshold
                state.intensity -= 1
                self._trigger_segment_impact(segment_id, state.color if state.intensity > 0 else "blue", state.intensity)
                if state.intensity == 0:
                    state.color = "blue"
                    state.clean_progress = 0.0
                    state.harvest_progress = 0.0
                    break
                threshold = self.spec.red_clean_thresholds[state.intensity - 1]
        elif state.color == "green" and state.intensity > 0:
            state.harvest_progress += distance * orb.harvest_rate
            threshold = self.spec.green_harvest_thresholds[state.intensity - 1]
            while state.intensity > 0 and state.harvest_progress >= threshold:
                state.harvest_progress -= threshold
                self.coins += self.spec.harvest_income_green[state.intensity - 1]
                state.intensity -= 1
                self._trigger_segment_impact(segment_id, state.color if state.intensity > 0 else "blue", state.intensity)
                if state.intensity == 0:
                    state.color = "blue"
                    state.clean_progress = 0.0
                    state.harvest_progress = 0.0
                    break
                threshold = self.spec.green_harvest_thresholds[state.intensity - 1]

    def _damage_enemies_on_segment(self, orb: Orb) -> None:
        for enemy in list(self.enemies.values()):
            if enemy.segment_id != orb.segment_id:
                continue
            if abs(enemy.distance_on_segment - orb.distance_on_segment) <= self.spec.visuals.enemy_radius * 2.0:
                enemy.hp -= orb.damage
                if enemy.hp <= 0:
                    self.enemies.pop(enemy.key, None)

    def _choose_next_segment(self, orb: Orb, node_id: str) -> tuple[str | None, str | None]:
        candidates = self._legal_segments_from_node(node_id, orb.from_node, orb.current_tier)
        if not candidates:
            if orb.forced_uturn_used or orb.from_node is None:
                return None, None
            orb.forced_uturn_used = True
            return orb.segment_id, orb.from_node

        tower = self.towers.get(orb.owner_tower_id)
        if orb.mode == "power" or tower is None:
            segment_id = self.random.choice(candidates)
        else:
            segment_id = self._select_segment_for_tower(tower, orb, node_id, candidates)
        segment = self.topology.segments[segment_id]
        next_node = segment.b if segment.a == node_id else segment.a
        return segment_id, next_node

    def _select_segment_for_tower(self, tower: TowerInstance, orb: Orb, node_id: str, candidates: list[str]) -> str:
        current_heading = self._heading(orb.from_node, node_id)
        if tower.archetype == "basic_tower" and orb.mode == "default":
            straightest = self._smallest_angle_segment(node_id, current_heading, candidates)
            if straightest is not None and self._angle_for_segment(node_id, current_heading, straightest) < 25:
                return straightest
            return self.random.choice(candidates)
        if tower.archetype == "basic_tower" and orb.mode == "secondary":
            home = self.topology.nodes[orb.home_node_id]
            ranked = []
            for segment_id in candidates:
                endpoint = self._far_endpoint(node_id, segment_id)
                node = self.topology.nodes[endpoint]
                distance = math.dist((home.x, home.y), (node.x, node.y))
                inside = distance <= 150.0
                edge = abs(150.0 - distance) if inside else distance
                enemy_adjacent = self._segment_enemy_count(segment_id) > 0
                non_red = self.segment_states[segment_id].color != "red"
                ranked.append((not inside, edge, -int(enemy_adjacent), -int(non_red), self.random.random(), segment_id))
            ranked.sort()
            return ranked[0][-1]
        if tower.archetype == "seed_tower" and orb.mode == "default":
            if self.random.random() < orb.turn_chance:
                turns = [item for item in candidates if self._angle_for_segment(node_id, current_heading, item) >= 30]
                if turns:
                    return self.random.choice(turns)
            return self.random.choice(candidates)
        if tower.archetype == "seed_tower" and orb.mode == "secondary":
            home = self.topology.nodes[orb.home_node_id]
            ranked = []
            for segment_id in candidates:
                endpoint = self._far_endpoint(node_id, segment_id)
                node = self.topology.nodes[endpoint]
                distance = math.dist((home.x, home.y), (node.x, node.y))
                ranked.append((distance > 160.0, distance, self.random.random(), segment_id))
            ranked.sort()
            return ranked[0][-1]
        if tower.archetype == "burst_tower" and orb.mode == "default":
            weights = []
            for segment_id in candidates:
                angle = self._angle_for_segment(node_id, current_heading, segment_id)
                weight = 0.35 if angle < 30 else 1.0 + orb.turn_chance
                weights.append(weight)
            return self.random.choices(candidates, weights=weights, k=1)[0]
        if tower.archetype == "burst_tower" and orb.mode == "secondary":
            ranked = sorted(
                candidates,
                key=lambda item: (
                    round(self._angle_for_segment(node_id, current_heading, item), 6),
                    self.random.random(),
                ),
            )[:2]
            if len(ranked) == 1:
                return ranked[0]
            bias = orb.burst_bias_forward or 0.70
            return ranked[0] if self.random.random() < bias else ranked[1]
        return self.random.choice(candidates)

    def _heading(self, a_id: str, b_id: str) -> tuple[float, float]:
        a = self.topology.nodes[a_id]
        b = self.topology.nodes[b_id]
        dx = b.x - a.x
        dy = b.y - a.y
        length = math.hypot(dx, dy) or 1.0
        return (dx / length, dy / length)

    def _angle_for_segment(self, node_id: str, current_heading: tuple[float, float], segment_id: str) -> float:
        endpoint = self._far_endpoint(node_id, segment_id)
        heading = self._heading(node_id, endpoint)
        dot = max(-1.0, min(1.0, current_heading[0] * heading[0] + current_heading[1] * heading[1]))
        return math.degrees(math.acos(dot))

    def _smallest_angle_segment(self, node_id: str, current_heading: tuple[float, float], candidates: list[str]) -> str | None:
        ranked = sorted(candidates, key=lambda item: self._angle_for_segment(node_id, current_heading, item))
        return ranked[0] if ranked else None

    def _far_endpoint(self, node_id: str, segment_id: str) -> str:
        segment = self.topology.segments[segment_id]
        return segment.b if segment.a == node_id else segment.a

    def _legal_segments_from_node(self, node_id: str, previous_node: str | None, max_tier: str) -> list[str]:
        allowed = allowed_tiers(max_tier)
        result = []
        for segment_id in self.topology.adjacency[node_id]:
            segment = self.topology.segments[segment_id]
            if segment.tier not in allowed:
                continue
            other = segment.b if segment.a == node_id else segment.a
            if previous_node is not None and other == previous_node:
                continue
            result.append(segment_id)
        return result

    def _segment_enemy_count(self, segment_id: str) -> int:
        return sum(1 for enemy in self.enemies.values() if enemy.segment_id == segment_id)

    def _update_enemies(self, dt: float) -> None:
        for enemy in list(self.enemies.values()):
            segment = self.topology.segments[enemy.segment_id]
            enemy.distance_on_segment += enemy.speed * dt
            while enemy.distance_on_segment >= segment.length:
                overflow = enemy.distance_on_segment - segment.length
                current_node = enemy.to_node
                if enemy.enemy_type == "corruption_seeder":
                    enemy.path_budget_remaining -= 1
                    if enemy.path_budget_remaining <= 0:
                        self._seed_red_at_node(current_node, 2)
                        self.enemies.pop(enemy.key, None)
                        break
                    next_segment_id, next_node = self._next_segment_for_seeder(enemy, current_node)
                else:
                    next_segment_id, next_node = self._next_segment_for_striker(enemy, current_node)
                    if next_segment_id is None:
                        self._resolve_striker_arrival(enemy, current_node)
                        self.enemies.pop(enemy.key, None)
                        break
                enemy.from_node = current_node
                enemy.to_node = next_node
                enemy.segment_id = next_segment_id
                enemy.distance_on_segment = overflow
                segment = self.topology.segments[enemy.segment_id]

    def _next_segment_for_seeder(self, enemy: Enemy, node_id: str) -> tuple[str, str]:
        candidates = self._legal_segments_from_node(node_id, enemy.from_node, "small")
        if not candidates:
            candidates = [enemy.segment_id]
        segment_id = self.random.choice(candidates)
        segment = self.topology.segments[segment_id]
        return segment_id, segment.b if segment.a == node_id else segment.a

    def _next_segment_for_striker(self, enemy: Enemy, node_id: str) -> tuple[str | None, str | None]:
        target_hardpoint = self._find_target_for_striker(enemy)
        if target_hardpoint is not None:
            enemy.target_hardpoint_id = target_hardpoint.hardpoint.key
            target_node_id = target_hardpoint.hardpoint.node_id
            route = self._shortest_path_nodes(node_id, target_node_id, "small")
            if len(route) < 2:
                return None, None
            next_node = route[1]
            segment_id = self._segment_between(node_id, next_node, "small")
            alternatives = self._alt_striker_segments(node_id, target_node_id, next_node)
            if alternatives and self.random.random() < self.spec.enemies["tower_striker"].path_turn_chance:
                segment_id = self.random.choice(alternatives)
                next_node = self._far_endpoint(node_id, segment_id)
            return segment_id, next_node
        target_segment_id = self._select_tower_striker_fallback_target()
        if target_segment_id is None:
            return None, None
        enemy.fallback_target_segment_id = target_segment_id
        target_node_id = self.topology.segments[target_segment_id].a
        route = self._shortest_path_nodes(node_id, target_node_id, "small")
        if len(route) < 2:
            return None, None
        next_node = route[1]
        segment_id = self._segment_between(node_id, next_node, "small")
        alternatives = self._alt_striker_segments(node_id, target_node_id, next_node)
        if alternatives and self.random.random() < self.spec.enemies["tower_striker"].path_turn_chance:
            segment_id = self.random.choice(alternatives)
            next_node = self._far_endpoint(node_id, segment_id)
        return segment_id, next_node

    def _resolve_striker_arrival(self, enemy: Enemy, node_id: str) -> None:
        if enemy.target_hardpoint_id and enemy.target_hardpoint_id in self.hardpoints:
            hardpoint_state = self.hardpoints[enemy.target_hardpoint_id]
            if self.power.active_hardpoint_id == enemy.target_hardpoint_id:
                self.power.hp -= self.spec.enemies["tower_striker"].tower_contact_damage
            elif hardpoint_state.tower is not None:
                hardpoint_state.tower.hp -= self.spec.enemies["tower_striker"].tower_contact_damage
        else:
            self._seed_red_at_node(node_id, 2)

    def _find_target_for_striker(self, enemy: Enemy) -> HardpointState | None:
        candidates = [
            hardpoint_state
            for hardpoint_state in self.hardpoints.values()
            if hardpoint_state.tower is not None or self.power.active_hardpoint_id == hardpoint_state.hardpoint.key
        ]
        if not candidates:
            return None
        current_node = self.topology.nodes[enemy.to_node]
        return min(
            candidates,
            key=lambda item: math.dist(
                (current_node.x, current_node.y),
                (
                    self.topology.nodes[item.hardpoint.node_id].x,
                    self.topology.nodes[item.hardpoint.node_id].y,
                ),
            ),
        )

    def _select_tower_striker_fallback_target(self) -> str | None:
        center = self.topology.center
        candidates = [
            segment_id
            for segment_id in self.topology.segments
            if not self._segment_is_perimeter(segment_id)
        ]
        if not candidates:
            return None
        ranked = sorted(
            candidates,
            key=lambda segment_id: (
                self.segment_states[segment_id].color == "red",
                math.dist(self.topology.segment_midpoint(segment_id), center),
                -self._segment_connectivity(segment_id),
                self.segment_states[segment_id].color != "green",
                self.random.random(),
            ),
        )
        return ranked[0]

    def _segment_is_perimeter(self, segment_id: str) -> bool:
        left, top, right, bottom = self.topology.playfield_rect
        segment = self.topology.segments[segment_id]
        for node_id in (segment.a, segment.b):
            node = self.topology.nodes[node_id]
            if (
                math.isclose(node.x, left)
                or math.isclose(node.x, right)
                or math.isclose(node.y, top)
                or math.isclose(node.y, bottom)
            ):
                return True
        return False

    def _segment_connectivity(self, segment_id: str) -> int:
        segment = self.topology.segments[segment_id]
        return len(self.topology.adjacency[segment.a]) + len(self.topology.adjacency[segment.b])

    def _seed_red_at_node(self, node_id: str, intensity: int) -> None:
        self.seed_pulses.append(SeedPulse(node_id=node_id, time_remaining=0.35, duration=0.35))
        for segment_id in self.topology.nodes[node_id].segment_ids:
            state = self.segment_states[segment_id]
            if state.color == "green":
                continue
            state.color = "red"
            state.intensity = max(state.intensity, intensity)
            state.clean_progress = 0.0
            state.harvest_progress = 0.0
            self._trigger_segment_impact(segment_id, state.color, state.intensity)
            return

    def _update_power(self, dt: float) -> None:
        if self.power.active_hardpoint_id is None:
            return
        self.power.time_remaining = max(0.0, self.power.time_remaining - dt)
        if self.power.hp <= 0 or self.power.time_remaining <= 0:
            self.power.active_hardpoint_id = None
            self.power.time_remaining = 0.0
            self.power.hp = 0.0
            self.power.suspended_tower = None
            self.power.fire_cooldown = 0.0

    def _update_spread(self, dt: float) -> None:
        self.spread_timer -= dt
        self.green_spread_timer -= dt
        red_due = False
        green_due = False
        if self.spread_timer <= 0:
            self.spread_timer += self.spec.spread_interval
            red_due = True
        if self.green_spread_timer <= 0:
            self.green_spread_timer += self.spec.green_spread_interval
            green_due = True
        if red_due or green_due:
            self._resolve_spread_step(red_due=red_due, green_due=green_due)

    def _resolve_spread_step(self, red_due: bool, green_due: bool) -> None:
        for tier in ("large", "medium", "small"):
            proposals: dict[str, set[str]] = {}
            if red_due:
                self._collect_spread_proposals("red", tier, proposals)
            if green_due:
                self._collect_spread_proposals("green", tier, proposals)
            for segment_id, colors in proposals.items():
                state = self.segment_states[segment_id]
                if "red" in colors and "green" in colors:
                    continue
                applied = next(iter(colors))
                if state.color == applied:
                    state.intensity = min(3, state.intensity + 1)
                elif state.color == "blue":
                    state.color = applied
                    state.intensity = 1
                state.clean_progress = 0.0
                state.harvest_progress = 0.0

    def _update_feedback_effects(self, dt: float) -> None:
        for segment_id in list(self.segment_impacts):
            impact = self.segment_impacts[segment_id]
            impact.time_remaining = max(0.0, impact.time_remaining - dt)
            if impact.time_remaining <= 0:
                self.segment_impacts.pop(segment_id, None)
        for pulse in list(self.seed_pulses):
            pulse.time_remaining = max(0.0, pulse.time_remaining - dt)
            if pulse.time_remaining <= 0:
                self.seed_pulses.remove(pulse)

    def _trigger_segment_impact(self, segment_id: str, color: str, intensity: int) -> None:
        self.segment_impacts[segment_id] = SegmentImpact(
            color=color,
            intensity=intensity,
            time_remaining=0.22,
            duration=0.22,
        )

    def _collect_spread_proposals(self, color: str, tier: str, proposals: dict[str, set[str]]) -> None:
        source_ids = [
            segment_id
            for segment_id, state in self.segment_states.items()
            if state.color == color and state.intensity > 0 and self.topology.segments[segment_id].tier == tier
        ]
        for segment_id in source_ids:
            segment = self.topology.segments[segment_id]
            state = self.segment_states[segment_id]
            chance = (
                self.spec.red_spread_chance_by_tier[segment.tier]
                if color == "red"
                else self.spec.green_spread_chance_by_tier[segment.tier]
            )
            if self.surge_time_remaining > 0 and color == "red":
                chance *= 1.5
            for neighbor_id in self._neighbor_segments(segment_id):
                if self.random.random() < chance:
                    proposals.setdefault(neighbor_id, set()).add(color)
            growth = self.spec.red_intensity_growth_chance if color == "red" else self.spec.green_intensity_growth_chance
            if state.intensity < 3 and self.random.random() < growth:
                state.intensity += 1
                state.clean_progress = 0.0
                state.harvest_progress = 0.0

    def _neighbor_segments(self, segment_id: str) -> set[str]:
        segment = self.topology.segments[segment_id]
        result = set()
        for node_id in (segment.a, segment.b):
            for other_id in self.topology.adjacency[node_id]:
                if other_id != segment_id:
                    result.add(other_id)
        return result

    def _spawn_enemies(self, dt: float) -> None:
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        interval = max(
            self.spec.spawn_interval_floor,
            self.spec.base_spawn_interval - (self.level - 1) * self.spec.spawn_rate_growth_per_level,
        )
        self.spawn_timer += interval
        spawn_count = max(1, round(1 + (self.level - 1) * self.spec.spawn_rate_growth_per_level))
        if self.surge_time_remaining > 0:
            spawn_count += 1
        for _ in range(spawn_count):
            self._spawn_enemy()

    def _spawn_enemy(self) -> None:
        enemy_spec = self.random.choices(
            list(self.spec.enemies.values()),
            weights=[enemy.spawn_weight for enemy in self.spec.enemies.values()],
            k=1,
        )[0]
        hardpoint = self.random.choice(self.topology.hardpoints)
        segment_id, to_node = self._pick_initial_segment(hardpoint.node_id, "small")
        if segment_id is None:
            return
        hp = enemy_spec.hp * (1 + (self.level - 1) * self.spec.enemy_hp_growth_per_level)
        enemy = Enemy(
            key=self.next_id("enemy"),
            enemy_type=enemy_spec.key,
            hp=hp,
            segment_id=segment_id,
            from_node=hardpoint.node_id,
            to_node=to_node,
            distance_on_segment=0.0,
            speed=enemy_spec.speed,
            initial_path_budget=enemy_spec.path_step_budget,
            path_budget_remaining=enemy_spec.path_step_budget,
        )
        self.enemies[enemy.key] = enemy

    def _shortest_path_nodes(self, start_node_id: str, end_node_id: str, max_tier: str) -> list[str]:
        if start_node_id == end_node_id:
            return [start_node_id]
        frontier = deque([start_node_id])
        came_from = {start_node_id: None}
        allowed = allowed_tiers(max_tier)
        while frontier:
            node_id = frontier.popleft()
            for segment_id in self.topology.adjacency[node_id]:
                segment = self.topology.segments[segment_id]
                if segment.tier not in allowed:
                    continue
                next_node = segment.b if segment.a == node_id else segment.a
                if next_node in came_from:
                    continue
                came_from[next_node] = node_id
                if next_node == end_node_id:
                    frontier.clear()
                    break
                frontier.append(next_node)
        if end_node_id not in came_from:
            return [start_node_id]
        path = [end_node_id]
        current = end_node_id
        while came_from[current] is not None:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _segment_between(self, a_id: str, b_id: str, max_tier: str) -> str:
        allowed = allowed_tiers(max_tier)
        for segment_id in self.topology.adjacency[a_id]:
            segment = self.topology.segments[segment_id]
            other = segment.b if segment.a == a_id else segment.a
            if other == b_id and segment.tier in allowed:
                return segment_id
        raise KeyError(f"No segment between {a_id} and {b_id}")

    def _alt_striker_segments(self, node_id: str, target_node_id: str, best_next_node: str) -> list[str]:
        best_route = self._shortest_path_nodes(best_next_node, target_node_id, "small")
        best_remaining = max(0, len(best_route) - 1)
        result = []
        for segment_id in self.topology.adjacency[node_id]:
            next_node = self._far_endpoint(node_id, segment_id)
            if next_node == node_id:
                continue
            route = self._shortest_path_nodes(next_node, target_node_id, "small")
            remaining = max(0, len(route) - 1)
            if remaining <= best_remaining:
                result.append(segment_id)
        return result

    def _trim_shot_history(self) -> None:
        cutoff = self.run_time - self.spec.shots_recent_window
        while self.shots_fired_times and self.shots_fired_times[0] < cutoff:
            self.shots_fired_times.popleft()

    def _destroy_tower(self, tower: TowerInstance) -> None:
        hardpoint_state = self.hardpoints[tower.hardpoint_id]
        hardpoint_state.tower = None
        self.towers.pop(tower.key, None)

    def tower_hp_value(self, tower_key: str) -> float:
        base = self.spec.towers[tower_key].hp
        level = self.global_upgrade_levels[tower_key]["hp"]
        return base * (1 + level * 0.20)

    def speed_multiplier(self, tower: TowerInstance) -> float:
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if tower.active_mode == "secondary" and mode_spec is not None:
            return mode_spec.snake_speed_multiplier
        return 1.0

    def damage_multiplier(self, tower: TowerInstance) -> float:
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if tower.active_mode == "secondary" and mode_spec is not None:
            return mode_spec.damage_multiplier
        return 1.0

    def shot_range_value(self, tower: TowerInstance, base_override: float | None = None) -> float:
        base = self.spec.towers[tower.archetype].shot_range if base_override is None else base_override
        if base <= 0:
            return base
        level = self.global_upgrade_levels[tower.archetype]["shot_range"]
        return base * (1 + level * 0.20)

    def fire_rate_value(self, tower: TowerInstance) -> float:
        level = self.global_upgrade_levels[tower.archetype]["fire_rate"]
        return self.spec.towers[tower.archetype].fire_rate * (1 + level * 0.15)

    def hit_damage_value(self, tower: TowerInstance) -> float:
        return self.spec.towers[tower.archetype].hit_damage * (
            1 + self.global_upgrade_levels[tower.archetype]["hit_damage"] * 0.20
        )

    def snake_speed_value(self, tower: TowerInstance) -> float:
        return self.spec.towers[tower.archetype].snake_speed * (
            1 + self.global_upgrade_levels[tower.archetype]["snake_speed"] * 0.12
        )

    def clean_multiplier(self, tower: TowerInstance) -> float:
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if tower.active_mode == "secondary" and mode_spec is not None:
            return mode_spec.clean_multiplier
        return 1.0

    def harvest_multiplier(self, tower: TowerInstance) -> float:
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if tower.active_mode == "secondary" and mode_spec is not None:
            return mode_spec.harvest_multiplier
        return 1.0

    def turn_chance(self, tower: TowerInstance) -> float:
        base = self.spec.towers[tower.archetype].turn_chance
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if tower.active_mode == "secondary" and mode_spec is not None and mode_spec.turn_chance_override is not None:
            return mode_spec.turn_chance_override
        return base

    def tower_grid_access_tier(self, tower: TowerInstance) -> str:
        start = self.spec.towers[tower.archetype].grid_access_tier_start
        level = self.global_upgrade_levels[tower.archetype]["grid_access_tier"]
        index = min(TIER_INDEX[start] + level, TIER_INDEX["small"])
        return {index: tier for tier, index in TIER_INDEX.items()}[index]

    def corruption_percent(self) -> float:
        numerator = 0.0
        denominator = 0.0
        for segment_id, segment in self.topology.segments.items():
            denominator += segment.length * 3.0
            state = self.segment_states[segment_id]
            if state.color == "red":
                numerator += segment.length * state.intensity
        if denominator <= 0:
            return 0.0
        return max(0.0, min(100.0, 100.0 * numerator / denominator))

    def action_availability(self) -> dict[str, tuple[bool, str]]:
        hardpoint = self.selected_hardpoint()
        tower = self.selected_action_tower()
        power_selected = self.selected_power_active()
        result: dict[str, tuple[bool, str]] = {}

        if hardpoint is None:
            no_selection = (False, "Select a hardpoint.")
            result["buy_secondary"] = no_selection
            result["swap_mode"] = no_selection
            result["fund_power"] = (self._can_fund_power(), self._fund_power_reason())
            result["deploy_power"] = (False, "Select a hardpoint.")
            for tower_key in self.spec.towers:
                result[f"build_{tower_key}"] = no_selection
            for stat_name in self.spec.upgrade_costs:
                result[f"upgrade_{stat_name}"] = no_selection
            return result

        for tower_key in self.spec.towers:
            result[f"build_{tower_key}"] = self._can_build(hardpoint, tower_key)
        result["buy_secondary"] = self._can_buy_secondary(tower, power_selected)
        result["swap_mode"] = self._can_swap_mode(tower, power_selected)
        for stat_name in self.spec.upgrade_costs:
            result[f"upgrade_{stat_name}"] = self._can_upgrade(tower, stat_name, power_selected)
        result["fund_power"] = (self._can_fund_power(), self._fund_power_reason())
        result["deploy_power"] = self._can_deploy_power(hardpoint)
        seed_ok = tower is not None and tower.archetype == "seed_tower" and not power_selected
        seed_reason = "" if seed_ok else ("Blocked during power override." if power_selected else "Select a Seed Tower.")
        result["seed_closest_plus"] = (seed_ok, seed_reason)
        result["seed_closest_minus"] = (seed_ok, seed_reason)
        result["seed_color_plus"] = (seed_ok, seed_reason)
        result["seed_color_minus"] = (seed_ok, seed_reason)
        result["seed_darkest_plus"] = (seed_ok, seed_reason)
        result["seed_darkest_minus"] = (seed_ok, seed_reason)
        return result

    def upgrade_preview(self) -> list[str]:
        tower = self.selected_action_tower()
        if tower is None:
            return []
        previews = []
        for stat_name in self.spec.upgrade_costs:
            previews.append(self._upgrade_preview_line(tower, stat_name))
        return previews

    def _can_build(self, hardpoint: HardpointState, tower_key: str) -> tuple[bool, str]:
        tower_spec = self.spec.towers[tower_key]
        if self.selected_power_active():
            return False, "Blocked during power override."
        if hardpoint.tower is not None:
            return False, "Hardpoint occupied."
        if self.coins < tower_spec.build_cost:
            return False, f"Need {tower_spec.build_cost} coins."
        return True, ""

    def _can_buy_secondary(self, tower: TowerInstance | None, power_selected: bool) -> tuple[bool, str]:
        if power_selected:
            return False, "Blocked during power override."
        if tower is None:
            return False, "Build a tower first."
        if tower.secondary_unlocked:
            return False, "Already unlocked."
        mode_spec = self.spec.towers[tower.archetype].secondary_mode
        if mode_spec is None:
            return False, "No secondary mode."
        if self.coins < mode_spec.purchase_cost:
            return False, f"Need {mode_spec.purchase_cost} coins."
        return True, ""

    def _can_swap_mode(self, tower: TowerInstance | None, power_selected: bool) -> tuple[bool, str]:
        if power_selected:
            return False, "Blocked during power override."
        if tower is None:
            return False, "Build a tower first."
        if not tower.secondary_unlocked:
            return False, "Buy secondary first."
        if tower.swap_cooldown > 0:
            return False, f"Cooldown {tower.swap_cooldown:.1f}s."
        return True, ""

    def _can_upgrade(self, tower: TowerInstance | None, stat_name: str, power_selected: bool) -> tuple[bool, str]:
        if power_selected:
            return False, "Blocked during power override."
        if tower is None:
            return False, "Build a tower first."
        if stat_name == "shot_range" and self.spec.towers[tower.archetype].shot_range <= 0:
            return False, "N/A for this tower."
        level = self.global_upgrade_levels[tower.archetype][stat_name]
        costs = self.spec.upgrade_costs[stat_name]
        if level >= len(costs):
            return False, "Maxed."
        cost = costs[level]
        if self.coins < cost:
            return False, f"Need {cost} coins."
        return True, ""

    def _can_fund_power(self) -> bool:
        return self.fund_power_preview()[0]

    def _fund_power_reason(self) -> str:
        return self.fund_power_preview()[1]

    def fund_power_preview(self) -> tuple[bool, str]:
        if self.power.active_hardpoint_id is not None:
            return False, "Blocked while active."
        if self.power.charged:
            return False, "Charge already stored."
        if self.power.funding_percent >= 100:
            return False, "Already fully funded."
        if self.coins < self.spec.power_funding_chunk_cost:
            return False, f"Need {self.spec.power_funding_chunk_cost} coins."
        return True, ""

    def _can_deploy_power(self, hardpoint: HardpointState) -> tuple[bool, str]:
        if self.power.active_hardpoint_id is not None:
            return False, "Power already active."
        if not self.power.charged:
            return False, "No stored charge."
        if hardpoint is None:
            return False, "Select a hardpoint."
        return True, ""

    def _upgrade_preview_line(self, tower: TowerInstance, stat_name: str) -> str:
        label = UPGRADE_DISPLAY[stat_name]
        level = self.global_upgrade_levels[tower.archetype][stat_name]
        costs = self.spec.upgrade_costs[stat_name]
        if level >= len(costs):
            return f"{label}: MAX"
        current, next_value = self._upgrade_values(tower, stat_name)
        return f"{label}: {current} -> {next_value}  ({costs[level]}c)"

    def _upgrade_values(self, tower: TowerInstance, stat_name: str) -> tuple[str, str]:
        base_level = self.global_upgrade_levels[tower.archetype][stat_name]
        if stat_name == "fire_rate":
            current = self.spec.towers[tower.archetype].fire_rate * (1 + base_level * 0.15)
            next_value = self.spec.towers[tower.archetype].fire_rate * (1 + (base_level + 1) * 0.15)
            return f"{current:.2f}", f"{next_value:.2f}"
        if stat_name == "hp":
            current = self.spec.towers[tower.archetype].hp * (1 + base_level * 0.20)
            next_value = self.spec.towers[tower.archetype].hp * (1 + (base_level + 1) * 0.20)
            return f"{current:.0f}", f"{next_value:.0f}"
        if stat_name == "snake_speed":
            current = self.spec.towers[tower.archetype].snake_speed * (1 + base_level * 0.12)
            next_value = self.spec.towers[tower.archetype].snake_speed * (1 + (base_level + 1) * 0.12)
            return f"{current:.1f}", f"{next_value:.1f}"
        if stat_name == "hit_damage":
            current = self.spec.towers[tower.archetype].hit_damage * (1 + base_level * 0.20)
            next_value = self.spec.towers[tower.archetype].hit_damage * (1 + (base_level + 1) * 0.20)
            return f"{current:.1f}", f"{next_value:.1f}"
        if stat_name == "shot_range":
            if self.spec.towers[tower.archetype].shot_range <= 0:
                return "n/a", "n/a"
            current = self.shot_range_value(tower)
            next_multiplier = 1 + (base_level + 1) * 0.20
            base = self.spec.towers[tower.archetype].shot_range
            next_value = base if base <= 0 else base * next_multiplier
            return f"{current:.0f}", f"{next_value:.0f}"
        if stat_name == "grid_access_tier":
            tiers = ["large", "medium", "small"]
            current = self.tower_grid_access_tier(tower)
            next_index = min(tiers.index(current) + 1, len(tiers) - 1)
            return current, tiers[next_index]
        return "?", "?"

    def hud_snapshot(self) -> dict[str, object]:
        return {
            "coins": self.coins,
            "corruption_percent": self.corruption_percent(),
            "failure_threshold": self.spec.corruption_failure_threshold,
            "active_orb_count": len(self.orbs),
            "shots_recent": len(self.shots_fired_times),
            "selected_object": self.selected_object_snapshot(),
            "action_availability": self.action_availability(),
            "upgrade_preview": self.upgrade_preview(),
            "power_percent": self.power.funding_percent,
            "power_charged": self.power.charged,
            "surge_active": self.surge_time_remaining > 0,
            "level": self.level,
            "level_time_remaining": self.level_timer,
            "game_over": self.game_over,
        }
