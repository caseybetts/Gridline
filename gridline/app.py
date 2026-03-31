from __future__ import annotations

from dataclasses import replace
import re
import tkinter as tk

from .simulation import GameSimulation, Orb
from .spec import GameSpec, load_game_spec
from .topology import Topology


def segment_position(topology: Topology, segment_id: str, from_node_id: str, distance: float) -> tuple[float, float]:
    segment = topology.segments[segment_id]
    a = topology.nodes[segment.a]
    b = topology.nodes[segment.b]
    length = max(1.0, segment.length)
    t = min(1.0, max(0.0, distance / length))
    if from_node_id == segment.a:
        return (a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)
    return (b.x + (a.x - b.x) * t, b.y + (a.y - b.y) * t)


def build_orb_trail_points(topology: Topology, orb: Orb, trail_length: float) -> list[tuple[float, float]]:
    head = segment_position(topology, orb.segment_id, orb.from_node, orb.distance_on_segment)
    if trail_length <= 0:
        return [head]

    points = [head]
    remaining = trail_length
    current_distance = max(0.0, orb.distance_on_segment)
    current_node_id = orb.from_node
    current_node = topology.nodes[current_node_id]

    if current_distance > 0:
        if current_distance >= remaining:
            progress = remaining / current_distance
            points.append(
                (
                    head[0] + (current_node.x - head[0]) * progress,
                    head[1] + (current_node.y - head[1]) * progress,
                )
            )
            return _dedupe_points(points)
        points.append((current_node.x, current_node.y))
        remaining -= current_distance

    history = list(orb.trail_nodes)
    if not history and orb.previous_node is not None:
        history = [orb.previous_node]

    for previous_node_id in history:
        previous_segment_id = _segment_between(topology, current_node_id, previous_node_id)
        if previous_segment_id is None:
            break
        previous_segment = topology.segments[previous_segment_id]
        previous_node = topology.nodes[previous_node_id]
        backtrack = min(remaining, previous_segment.length)
        progress = backtrack / max(1.0, previous_segment.length)
        points.append(
            (
                current_node.x + (previous_node.x - current_node.x) * progress,
                current_node.y + (previous_node.y - current_node.y) * progress,
            )
        )
        remaining -= backtrack
        if remaining <= 0:
            break
        current_node_id = previous_node_id
        current_node = previous_node
    return _dedupe_points(points)


def _segment_between(topology: Topology, first_node_id: str, second_node_id: str) -> str | None:
    for segment_id in topology.adjacency.get(first_node_id, ()):
        segment = topology.segments[segment_id]
        if segment.a == second_node_id or segment.b == second_node_id:
            return segment_id
    return None


def _dedupe_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    deduped: list[tuple[float, float]] = []
    for point in points:
        if not deduped or deduped[-1] != point:
            deduped.append(point)
    return deduped


def build_faded_trail_segments(points: list[tuple[float, float]], segment_length: float = 14.0) -> list[tuple[tuple[float, float], tuple[float, float], float]]:
    if len(points) < 2:
        return []
    sampled = [points[0]]
    remaining = segment_length
    current = points[0]
    for point in points[1:]:
        start = current
        end = point
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = ((dx * dx) + (dy * dy)) ** 0.5
        if distance <= 0:
            current = end
            continue
        traveled = 0.0
        while traveled + remaining < distance:
            ratio = (traveled + remaining) / distance
            sampled.append((start[0] + dx * ratio, start[1] + dy * ratio))
            traveled += remaining
            remaining = segment_length
        remaining -= distance - traveled
        current = end
        if remaining <= 0.001:
            sampled.append(end)
            remaining = segment_length
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    segment_count = max(1, len(sampled) - 1)
    return [
        (sampled[index], sampled[index + 1], 1.0 - (index / segment_count))
        for index in range(segment_count)
    ]


def blend_hex(color: str, target: str, amount: float) -> str:
    amount = min(1.0, max(0.0, amount))
    color_channels = [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    target_channels = [int(target[index:index + 2], 16) for index in (1, 3, 5)]
    blended = [
        round(target_channel + (color_channel - target_channel) * amount)
        for color_channel, target_channel in zip(color_channels, target_channels)
    ]
    return "#{:02X}{:02X}{:02X}".format(*blended)


def enemy_render_color(app: "GridlineApp", enemy) -> str:
    if enemy.enemy_type != "corruption_seeder":
        return app.spec.visuals.enemy_striker
    budget = max(1, enemy.initial_path_budget)
    progress = 1.0 - (enemy.path_budget_remaining / budget)
    return blend_hex(app.spec.visuals.red_levels[2], app.spec.visuals.red_levels[0], progress)


class GridlineApp:
    def __init__(self, spec: GameSpec | None = None) -> None:
        self.spec = spec or load_game_spec()
        self.root = tk.Tk()
        self.root.title("Gridline MVP")
        self.root.geometry(f"{self.spec.width}x{self.spec.height}")
        self.root.configure(bg=self.spec.visuals.background)
        self.fullscreen = False

        self.main_frame = tk.Frame(self.root, bg=self.spec.visuals.background)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=self.spec.visuals.background,
            highlightthickness=0,
            width=self.spec.width - self.spec.visuals.sidebar_width,
            height=self.spec.height,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sidebar = tk.Frame(self.main_frame, bg=self.spec.visuals.sidebar, width=self.spec.visuals.sidebar_width)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.status_text = tk.StringVar()
        self.detail_text = tk.StringVar()
        self.feedback_text = tk.StringVar()
        self.upgrade_text = tk.StringVar()
        self.action_buttons: dict[str, tk.Button] = {}
        self.utility_buttons: dict[str, tk.Button] = {}
        self.action_groups: dict[str, tk.Frame] = {}
        self.action_group_headers: dict[str, tk.Label] = {}
        self.action_group_keys: dict[str, list[str]] = {}
        self._last_action_selection_signature: tuple[str | None, str] | None = None
        self._build_sidebar()
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.tick_ms = int(1000 / self.spec.simulation_tick_rate)
        self.loop_running = False
        self.root.update_idletasks()
        self.sim = GameSimulation(self._runtime_spec_for_canvas())

    def _build_sidebar(self) -> None:
        label_style = {
            "bg": self.spec.visuals.sidebar,
            "fg": self.spec.visuals.text,
            "anchor": "w",
            "justify": "left",
        }
        tk.Label(self.sidebar, text="Gridline", font=("Consolas", 18, "bold"), **label_style).pack(fill=tk.X, padx=16, pady=(16, 8))

        status_frame = tk.Frame(self.sidebar, bg=self.spec.visuals.sidebar)
        status_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        self._section_label(status_frame, "Run Status").pack(fill=tk.X, pady=(0, 4))
        tk.Label(status_frame, textvariable=self.status_text, font=("Consolas", 11), **label_style).pack(fill=tk.X)

        details_frame = tk.Frame(self.sidebar, bg=self.spec.visuals.sidebar)
        details_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        details_frame.pack_propagate(False)
        details_frame.configure(height=240)
        self._section_label(details_frame, "Selection").pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            details_frame,
            textvariable=self.detail_text,
            font=("Consolas", 10),
            wraplength=self.spec.visuals.sidebar_width - 32,
            **label_style,
        ).pack(fill=tk.X)
        tk.Label(
            details_frame,
            textvariable=self.feedback_text,
            font=("Consolas", 10),
            wraplength=self.spec.visuals.sidebar_width - 32,
            fg="#F2C46D",
            bg=self.spec.visuals.sidebar,
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, pady=(6, 0))
        tk.Label(
            details_frame,
            textvariable=self.upgrade_text,
            font=("Consolas", 9),
            wraplength=self.spec.visuals.sidebar_width - 32,
            **label_style,
        ).pack(fill=tk.X, pady=(6, 0))

        actions_shell = tk.Frame(self.sidebar, bg=self.spec.visuals.sidebar)
        actions_shell.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self._section_label(actions_shell, "Actions").pack(fill=tk.X, pady=(0, 4))
        self.action_canvas = tk.Canvas(actions_shell, bg=self.spec.visuals.sidebar, highlightthickness=0, bd=0)
        self.action_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.action_scrollbar = tk.Scrollbar(actions_shell, orient=tk.VERTICAL, command=self.action_canvas.yview)
        self.action_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_canvas.configure(yscrollcommand=self.action_scrollbar.set)
        self.action_inner = tk.Frame(self.action_canvas, bg=self.spec.visuals.sidebar)
        self.action_canvas_window = self.action_canvas.create_window((0, 0), window=self.action_inner, anchor="nw")
        self.action_inner.bind("<Configure>", self._sync_action_scrollregion)
        self.action_canvas.bind("<Configure>", self._sync_action_canvas_width)

        self._build_action_group(
            "build",
            "Build",
            [
                ("build_basic_tower", "Basic", lambda: self.sim.build_tower("basic_tower")),
                ("build_seed_tower", "Seed", lambda: self.sim.build_tower("seed_tower")),
                ("build_burst_tower", "Burst", lambda: self.sim.build_tower("burst_tower")),
            ],
            columns=3,
        )
        self._build_action_group(
            "tower",
            "Tower Controls",
            [
                ("buy_secondary", "Buy Mode", lambda: self.sim.purchase_secondary_mode()),
                ("swap_mode", "Swap Mode", lambda: self.sim.toggle_selected_mode()),
                ("upgrade_fire_rate", "Fire Rate", lambda: self.sim.upgrade_selected_tower_type("fire_rate")),
                ("upgrade_hp", "Upgrade HP", lambda: self.sim.upgrade_selected_tower_type("hp")),
                ("upgrade_snake_speed", "Snake Speed", lambda: self.sim.upgrade_selected_tower_type("snake_speed")),
                ("upgrade_hit_damage", "Upgrade Damage", lambda: self.sim.upgrade_selected_tower_type("hit_damage")),
                ("upgrade_shot_range", "Shot Range", lambda: self.sim.upgrade_selected_tower_type("shot_range")),
                ("upgrade_grid_access_tier", "Grid Tier", lambda: self.sim.upgrade_selected_tower_type("grid_access_tier")),
            ],
            columns=2,
        )
        self._build_action_group(
            "seed",
            "Seed Levers",
            [
                ("seed_closest_plus", "Close +5", lambda: self.sim.adjust_seed_lever("closest", 5)),
                ("seed_closest_minus", "Close -5", lambda: self.sim.adjust_seed_lever("closest", -5)),
                ("seed_color_plus", "Red +5", lambda: self.sim.adjust_seed_lever("color", 5)),
                ("seed_color_minus", "Red -5", lambda: self.sim.adjust_seed_lever("color", -5)),
                ("seed_darkest_plus", "Dark +5", lambda: self.sim.adjust_seed_lever("darkest", 5)),
                ("seed_darkest_minus", "Dark -5", lambda: self.sim.adjust_seed_lever("darkest", -5)),
            ],
            columns=2,
        )
        self._build_action_group(
            "power",
            "Power",
            [
                ("fund_power", "Fund +10%", lambda: self.sim.fund_power()),
                ("deploy_power", "Deploy", lambda: self.sim.deploy_power_to_selected()),
            ],
            columns=2,
        )

        utility_frame = tk.Frame(self.sidebar, bg=self.spec.visuals.sidebar)
        utility_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        self._section_label(utility_frame, "Menu").pack(fill=tk.X, pady=(0, 4))
        new_game_button = self._make_button(utility_frame, "new_game", "New Game", self._new_game)
        new_game_button.pack(fill=tk.X, pady=3)
        self.utility_buttons["new_game"] = new_game_button

    def _run_action(self, key: str, command) -> None:
        availability = self.sim.action_availability()
        if key in availability and not availability[key][0]:
            self.feedback_text.set(availability[key][1])
            self._refresh_sidebar()
            return
        before_snapshot = self.sim.selected_object_snapshot()
        before_power_percent = self.sim.power.funding_percent
        command()
        self.feedback_text.set(self._success_feedback(key, before_snapshot, before_power_percent))
        self._refresh_sidebar()

    def _build_action_group(self, group_key: str, title: str, actions: list[tuple[str, str, object]], columns: int = 1) -> None:
        group_frame = tk.Frame(self.action_inner, bg=self.spec.visuals.sidebar)
        header = self._section_label(group_frame, title)
        header.pack(fill=tk.X, pady=(0, 4))
        button_shell = tk.Frame(group_frame, bg=self.spec.visuals.sidebar)
        button_shell.pack(fill=tk.X)
        for column in range(columns):
            button_shell.grid_columnconfigure(column, weight=1, uniform=f"{group_key}_actions")
        keys: list[str] = []
        wraplength = self._button_wraplength(columns)
        for key, label, command in actions:
            button = self._make_button(button_shell, key, label, command, wraplength)
            index = len(keys)
            button.grid(
                row=index // columns,
                column=index % columns,
                sticky="ew",
                padx=3,
                pady=3,
            )
            self.action_buttons[key] = button
            keys.append(key)
        group_frame.pack(fill=tk.X, pady=(0, 10))
        self.action_groups[group_key] = group_frame
        self.action_group_headers[group_key] = header
        self.action_group_keys[group_key] = keys

    def _button_wraplength(self, columns: int) -> int:
        inner_width = self.spec.visuals.sidebar_width - 32
        cell_width = max(88, (inner_width - max(0, columns - 1) * 6) // max(1, columns))
        return max(56, cell_width - 28)

    def _make_button(self, parent: tk.Widget, key: str, label: str, command, wraplength: int | None = None) -> tk.Button:
        if wraplength is None:
            wraplength = self._button_wraplength(1)
        return tk.Button(
            parent,
            text=label,
            command=lambda key=key, command=command: self._run_action(key, command),
            bg="#132235",
            fg=self.spec.visuals.text,
            activebackground="#1C3654",
            activeforeground=self.spec.visuals.text,
            relief=tk.FLAT,
            disabledforeground="#6F8195",
            anchor="w",
            justify="left",
            wraplength=wraplength,
            height=2,
            padx=10,
            pady=6,
        )

    def _section_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=("Consolas", 10, "bold"),
            bg=self.spec.visuals.sidebar,
            fg=self.spec.visuals.muted_text,
            anchor="w",
            justify="left",
        )

    def _sync_action_scrollregion(self, _event=None) -> None:
        self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all"))

    def _sync_action_canvas_width(self, event) -> None:
        self.action_canvas.itemconfigure(self.action_canvas_window, width=event.width)

    def _toggle_fullscreen(self, _event=None) -> None:
        if not self.spec.fullscreen_toggle_enabled:
            return
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def _on_canvas_click(self, event) -> None:
        self.sim.click_world(event.x, event.y)
        self._refresh_sidebar()

    def _new_game(self) -> None:
        should_restart_loop = not self.loop_running or self.sim.game_over
        self.root.update_idletasks()
        self.sim = GameSimulation(self._runtime_spec_for_canvas())
        self._render()
        self._refresh_sidebar()
        if should_restart_loop:
            self._loop()

    def run(self) -> None:
        self._loop()
        self.root.mainloop()

    def _loop(self) -> None:
        self.loop_running = True
        self.sim.update(1.0 / self.spec.simulation_tick_rate)
        self._render()
        self._refresh_sidebar()
        if not self.sim.game_over:
            self.root.after(self.tick_ms, self._loop)
        else:
            self.loop_running = False

    def _refresh_sidebar(self) -> None:
        hud = self.sim.hud_snapshot()
        recent_harvest = hud["recent_harvest_event"]
        self.status_text.set(
            "\n".join(
                [
                    f"Pressure: {self._pressure_badge(hud)}",
                    f"Corruption: {self._meter_bar(hud['corruption_percent'], hud['failure_threshold'])} {hud['corruption_percent']:.1f}% / {hud['failure_threshold']:.0f}%",
                    f"Coins: {hud['coins']}",
                    f"Power: {self._power_status_text(hud)}",
                    f"Level: {hud['level']}  Next: {hud['level_time_remaining']:.1f}s",
                    f"Orbs: {hud['active_orb_count']}  Shots/s: {hud['shots_recent']}",
                    f"Harvest: {self._recent_harvest_text(recent_harvest)}",
                    f"Surge: {'ACTIVE' if hud['surge_active'] else 'idle'}",
                    "Status: GAME OVER" if hud["game_over"] else "Status: running",
                ]
            )
        )
        hardpoint = self.sim.selected_hardpoint()
        if hardpoint is None:
            self.detail_text.set("Select a hardpoint on the perimeter to build, upgrade, or deploy power.")
            self.upgrade_text.set("")
            self._update_button_states(hud["selected_object"], hud["action_availability"])
            return
        selected = hud["selected_object"]
        lines = [f"Selected: {hardpoint.hardpoint.key} ({hardpoint.hardpoint.side})"]
        if selected["kind"] == "power":
            fire_text = "READY" if selected["fire_ready"] else f"{selected['fire_cooldown']:.1f}s"
            lines.extend(
                [
                    f"State: {selected['name']}",
                    f"HP: {selected['hp']:.0f}/{selected['max_hp']:.0f}",
                    f"Fire: {self._state_badge(selected['fire_ready'], 'READY', fire_text)}",
                    f"Time Left: {selected['time_remaining']:.1f}s",
                    f"Economy: free shots  Harvest {self.spec.power_harvest_per_unit_distance:.3f}/u",
                    f"Suspended Tower: {selected['underlying_tower_name'] or 'none'}",
                ]
            )
        elif selected["kind"] == "tower":
            tower = selected["tower"]
            fire_text = "READY" if selected["fire_ready"] else f"{selected['fire_cooldown']:.1f}s"
            swap_text = f"{selected['swap_cooldown']:.1f}s"
            economy = hud["selected_tower_economy"]
            lines.extend(
                [
                    f"Tower: {selected['name']}",
                    f"HP: {selected['hp']:.0f}/{selected['max_hp']:.0f}",
                    f"Mode: {selected['mode_name']}",
                    f"Fire: {self._state_badge(selected['fire_ready'], 'READY', fire_text)}",
                    f"{selected['secondary_mode_name']} unlocked: {'Yes' if selected['secondary_unlocked'] else 'No'}",
                    f"Swap: {self._state_badge(selected['swap_cooldown'] <= 0, 'READY', swap_text)}",
                ]
            )
            if economy is not None:
                lines.extend(
                    [
                        f"Economy: {economy['shot_cost']:.1f}c/shot  Clean {economy['clean_per_unit']:.3f}/u",
                        f"Harvest: {economy['harvest_per_unit']:.3f}/u  Recent +{economy['recent_harvest_income']}c / {economy['window_seconds']:.0f}s",
                    ]
                )
            if tower.archetype == "seed_tower":
                lines.extend(
                    [
                        f"Closest/Random: {tower.seed_closest_vs_random}/{100 - tower.seed_closest_vs_random}",
                        f"Red/Green: {tower.seed_red_vs_green}/{100 - tower.seed_red_vs_green}",
                        f"Darkest/Random: {tower.seed_darkest_vs_random}/{100 - tower.seed_darkest_vs_random}",
                    ]
                )
        else:
            lines.extend(
                [
                    "Tower: empty",
                    "Build priorities:",
                    *self._build_option_summaries(),
                ]
            )
        self.detail_text.set("\n".join(lines))
        self.upgrade_text.set("\n".join(hud["upgrade_preview"]))
        self._update_button_states(hud["selected_object"], hud["action_availability"])
        self._maybe_reset_action_scroll(selected)

    def _update_button_states(self, selected: dict[str, object], availability: dict[str, tuple[bool, str]]) -> None:
        context = selected.get("kind", "none")
        self._update_context_action_labels(selected, availability)
        tower = selected.get("tower")
        active_groups = {"power"}
        if context in {"none", "empty"}:
            active_groups.add("build")
        elif context == "tower":
            active_groups.add("tower")
            if tower is not None and tower.archetype == "seed_tower":
                active_groups.add("seed")
        elif context == "power":
            active_groups.add("power")

        for group_key, header in self.action_group_headers.items():
            header.configure(fg=self.spec.visuals.text if group_key in active_groups else self.spec.visuals.muted_text)

        for key, button in self.action_buttons.items():
            enabled, _reason = availability.get(key, (True, ""))
            button.configure(state=tk.NORMAL if enabled else tk.DISABLED)
        for button in self.utility_buttons.values():
            button.configure(state=tk.NORMAL)

    def _update_context_action_labels(self, selected: dict[str, object], availability: dict[str, tuple[bool, str]]) -> None:
        buy_label = "Buy Mode"
        swap_label = "Swap Mode"
        build_basic_label = f"Basic | {self.spec.towers['basic_tower'].build_cost}c"
        build_seed_label = f"Seed | {self.spec.towers['seed_tower'].build_cost}c"
        build_burst_label = f"Burst | {self.spec.towers['burst_tower'].build_cost}c"
        fund_power_label = f"Fund +10% | {self.spec.power_funding_chunk_cost}c"
        deploy_power_label = "Deploy"
        if selected.get("kind") == "tower":
            secondary_mode_name = selected.get("secondary_mode_name")
            if secondary_mode_name:
                buy_label = f"Buy {self._short_mode_name(str(secondary_mode_name))}"
                if selected.get("mode") == "secondary":
                    swap_label = "To Default"
                else:
                    swap_label = f"To {self._short_mode_name(str(secondary_mode_name))}"
        if self.sim.power.charged:
            deploy_power_label = "Deploy | Ready"
        elif self.sim.power.active_hardpoint_id is not None:
            deploy_power_label = f"Deploy | {self.sim.power.time_remaining:.1f}s"
        label_map = {
            "buy_secondary": buy_label,
            "swap_mode": swap_label,
            "build_basic_tower": build_basic_label,
            "build_seed_tower": build_seed_label,
            "build_burst_tower": build_burst_label,
            "fund_power": fund_power_label,
            "deploy_power": deploy_power_label,
        }
        for key, label in label_map.items():
            enabled, reason = availability.get(key, (True, ""))
            self.action_buttons[key].configure(text=self._action_label(label, enabled, reason))

    def _recent_harvest_text(self, recent_harvest: dict[str, object] | None) -> str:
        if recent_harvest is None:
            return "no recent income"
        return (
            f"+{recent_harvest['amount']}c via {recent_harvest['tower_name']} / "
            f"{recent_harvest['mode_name']} ({recent_harvest['age']:.1f}s)"
        )

    def _maybe_reset_action_scroll(self, selected: dict[str, object]) -> None:
        selection_signature = (self.sim.selected_hardpoint_id, str(selected.get("kind", "none")))
        if selection_signature == self._last_action_selection_signature:
            return
        self._last_action_selection_signature = selection_signature
        if selected.get("kind") != "empty":
            return
        self.action_canvas.after_idle(lambda: self.action_canvas.yview_moveto(0.0))

    def _power_status_text(self, hud: dict[str, object]) -> str:
        if self.sim.power.active_hardpoint_id is not None:
            return f"[ACTIVE] {self._meter_bar(self.sim.power.time_remaining, self.spec.power_duration)} {self.sim.power.time_remaining:.1f}s"
        if hud["power_charged"]:
            return f"[READY] {self._meter_bar(10, 10)} 100%"
        return f"[FUNDING] {self._meter_bar(hud['power_percent'], 100)} {hud['power_percent']}%"

    def _build_option_summaries(self) -> list[str]:
        return [
            f"- Basic Tower ({self.spec.towers['basic_tower'].build_cost}c): reliable generalist; best defensive mode host.",
            f"- Seed Tower ({self.spec.towers['seed_tower'].build_cost}c): strongest remote corruption response and map reach.",
            f"- Burst Tower ({self.spec.towers['burst_tower'].build_cost}c): strongest local interception and panic control.",
        ]

    def _action_label(self, label: str, enabled: bool, reason: str) -> str:
        if enabled or not reason:
            return label
        return f"{label} | {self._compact_reason(reason)}"

    def _short_mode_name(self, mode_name: str) -> str:
        return mode_name.replace(" Mode", "")

    def _compact_reason(self, reason: str) -> str:
        text = reason.strip().rstrip(".")
        coin_match = re.fullmatch(r"Need (\d+) coins", text)
        if coin_match is not None:
            return f"Need {coin_match.group(1)}c"
        replacements = {
            "Blocked during power override": "Blocked: power active",
            "Select a hardpoint": "Select hardpoint",
            "Select a Seed Tower": "Select Seed Tower",
            "Already fully funded": "Already funded",
            "Hardpoint occupied": "Occupied",
            "No stored charge": "Need stored charge",
            "Charge already stored": "Charge stored",
            "Already active": "Already active",
            "Power already active": "Power active",
        }
        return replacements.get(text, text)

    def _success_feedback(
        self,
        key: str,
        before_snapshot: dict[str, object],
        before_power_percent: int,
    ) -> str:
        if key.startswith("build_"):
            return f"Built {key.removeprefix('build_').replace('_tower', '').replace('_', ' ').title()}."
        if key == "buy_secondary":
            mode_name = before_snapshot.get("secondary_mode_name", "Secondary")
            return f"{mode_name} unlocked."
        if key == "swap_mode":
            after_snapshot = self.sim.selected_object_snapshot()
            mode_name = after_snapshot.get("mode_name", "Mode")
            return f"Switched to {mode_name}."
        if key.startswith("upgrade_"):
            return f"Upgraded {key.removeprefix('upgrade_').replace('_', ' ').title()}."
        if key == "fund_power":
            return f"Power funding: {before_power_percent}% -> {self.sim.power.funding_percent}%."
        if key == "deploy_power":
            return "Power deployed."
        return ""

    def _meter_bar(self, current: float, maximum: float, width: int = 10) -> str:
        if maximum <= 0:
            return "[" + "." * width + "]"
        ratio = max(0.0, min(1.0, current / maximum))
        filled = int(round(ratio * width))
        if ratio > 0 and filled == 0:
            filled = 1
        return "[" + "#" * filled + "." * (width - filled) + "]"

    def _pressure_badge(self, hud: dict[str, object]) -> str:
        if hud["game_over"]:
            return "[FAILED]"
        ratio = 0.0 if hud["failure_threshold"] <= 0 else hud["corruption_percent"] / hud["failure_threshold"]
        if ratio >= 0.85:
            return "[CRITICAL]"
        if ratio >= 0.55:
            return "[HIGH]"
        if ratio >= 0.25:
            return "[RISING]"
        return "[STABLE]"

    def _state_badge(self, ready: bool, ready_text: str, waiting_text: str) -> str:
        return f"[{ready_text}]" if ready else f"[WAIT] {waiting_text}"

    def _render(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill=self.spec.visuals.playfield_overlay, outline="")
        for segment_id, segment in self.sim.topology.segments.items():
            state = self.sim.segment_states[segment_id]
            a = self.sim.topology.nodes[segment.a]
            b = self.sim.topology.nodes[segment.b]
            self.canvas.create_line(a.x, a.y, b.x, b.y, fill=self._segment_color(segment.tier, state.color, state.intensity), width={"large": self.spec.visuals.large_line_width, "medium": self.spec.visuals.medium_line_width, "small": self.spec.visuals.small_line_width}[segment.tier])
            impact = self.sim.segment_impacts.get(segment_id)
            if impact is not None:
                effect_strength = impact.time_remaining / impact.duration if impact.duration > 0 else 0.0
                flash_color = self._impact_color(impact.color, impact.intensity, impact.effect, effect_strength)
                self.canvas.create_line(
                    a.x,
                    a.y,
                    b.x,
                    b.y,
                    fill=flash_color,
                    width={"large": self.spec.visuals.large_line_width, "medium": self.spec.visuals.medium_line_width, "small": self.spec.visuals.small_line_width}[segment.tier] + 3.0 * effect_strength,
                )

        for hardpoint_state in self.sim.hardpoints.values():
            node = self.sim.topology.nodes[hardpoint_state.hardpoint.node_id]
            fill = "#1B3145" if hardpoint_state.tower is not None else "#10202F"
            outline = "#8BD3FF" if self.sim.selected_hardpoint_id == hardpoint_state.hardpoint.key else "#30506B"
            self.canvas.create_oval(node.x - self.spec.visuals.hardpoint_radius, node.y - self.spec.visuals.hardpoint_radius, node.x + self.spec.visuals.hardpoint_radius, node.y + self.spec.visuals.hardpoint_radius, fill=fill, outline=outline, width=2)
            if hardpoint_state.tower is not None:
                color = {"basic_tower": "#A8B9CC", "seed_tower": "#9DE0B1", "burst_tower": "#FFD08A"}[hardpoint_state.tower.archetype]
                self.canvas.create_oval(node.x - 5, node.y - 5, node.x + 5, node.y + 5, fill=color, outline="")
            if self.sim.power.active_hardpoint_id == hardpoint_state.hardpoint.key:
                self.canvas.create_oval(node.x - 14, node.y - 14, node.x + 14, node.y + 14, outline="#FCEB8B", width=2)

        for orb in self.sim.orbs.values():
            trail_points = build_orb_trail_points(self.sim.topology, orb, self._orb_trail_length(orb))
            for start, end, intensity in build_faded_trail_segments(trail_points):
                glow_color = blend_hex(self.spec.visuals.orb_head, self.spec.visuals.playfield_overlay, 0.18 + intensity * 0.45)
                trail_color = blend_hex(self.spec.visuals.orb_trail, self.spec.visuals.playfield_overlay, 0.08 + intensity * 0.72)
                self.canvas.create_line(
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                    fill=glow_color,
                    width=self.spec.visuals.orb_trail_width * (1.2 + intensity * 0.9),
                    capstyle=tk.ROUND,
                )
                self.canvas.create_line(
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                    fill=trail_color,
                    width=self.spec.visuals.orb_trail_width * (0.65 + intensity * 0.35),
                    capstyle=tk.ROUND,
                )
            x, y = trail_points[0]
            glow_radius = self.spec.visuals.orb_head_radius * 1.8
            self.canvas.create_oval(
                x - glow_radius,
                y - glow_radius,
                x + glow_radius,
                y + glow_radius,
                fill=self.spec.visuals.orb_trail,
                outline="",
            )
            self.canvas.create_oval(x - self.spec.visuals.orb_head_radius, y - self.spec.visuals.orb_head_radius, x + self.spec.visuals.orb_head_radius, y + self.spec.visuals.orb_head_radius, fill=self.spec.visuals.orb_head, outline="")

        for flight in self.sim.seed_flights.values():
            x, y = self._seed_flight_position(flight)
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#F4E7A1", outline="")

        for enemy in self.sim.enemies.values():
            x, y = self._segment_position(enemy.segment_id, enemy.from_node, enemy.distance_on_segment)
            color = enemy_render_color(self, enemy)
            self.canvas.create_oval(x - self.spec.visuals.enemy_radius, y - self.spec.visuals.enemy_radius, x + self.spec.visuals.enemy_radius, y + self.spec.visuals.enemy_radius, fill=color, outline="")

        for pulse in self.sim.seed_pulses:
            node = self.sim.topology.nodes[pulse.node_id]
            progress = 1.0 - (pulse.time_remaining / pulse.duration if pulse.duration > 0 else 1.0)
            radius = 8.0 + progress * 18.0
            color = blend_hex(self.spec.visuals.red_levels[1], self.spec.visuals.playfield_overlay, 0.9 - progress * 0.7)
            self.canvas.create_oval(node.x - radius, node.y - radius, node.x + radius, node.y + radius, outline=color, width=max(1.0, 3.0 - progress * 2.0))

        for popup in self.sim.harvest_popups:
            x, y = self.sim.topology.segment_midpoint(popup.segment_id)
            progress = 1.0 - (popup.time_remaining / popup.duration if popup.duration > 0 else 1.0)
            text_y = y - (12.0 + progress * 18.0)
            color = blend_hex("#FFD779", self.spec.visuals.playfield_overlay, 0.95 - progress * 0.55)
            self.canvas.create_text(
                x,
                text_y,
                text=popup.label,
                fill=color,
                font=("Consolas", 10, "bold"),
            )

        self.canvas.create_text(16, 16, anchor="nw", fill=self.spec.visuals.text, font=("Consolas", 12, "bold"), text=f"Coins {self.sim.coins}   Corruption {self.sim.corruption_percent():.1f}%   Orbs {len(self.sim.orbs)}   Enemies {len(self.sim.enemies)}")
        if self.sim.surge_time_remaining > 0:
            self.canvas.create_text(16, 36, anchor="nw", fill=self.spec.visuals.warning, font=("Consolas", 11, "bold"), text=f"SURGE ACTIVE {self.sim.surge_time_remaining:.1f}s")
        if self.sim.game_over:
            self.canvas.create_text(self.canvas.winfo_width() / 2, 36, fill=self.spec.visuals.critical, font=("Consolas", 16, "bold"), text="GRID FAILURE")

    def _segment_position(self, segment_id: str, from_node_id: str, distance: float) -> tuple[float, float]:
        return segment_position(self.sim.topology, segment_id, from_node_id, distance)

    def _segment_color(self, tier: str, color: str, intensity: int) -> str:
        if color == "red" and intensity > 0:
            return self.spec.visuals.red_levels[intensity - 1]
        if color == "green" and intensity > 0:
            return self.spec.visuals.green_levels[intensity - 1]
        return {"large": self.spec.visuals.neutral_large, "medium": self.spec.visuals.neutral_medium, "small": self.spec.visuals.neutral_small}[tier]

    def _impact_color(self, color: str, intensity: int, effect: str, effect_strength: float) -> str:
        if effect == "clean":
            base = self.spec.visuals.neutral_large if color == "blue" else self.spec.visuals.green_levels[0]
            return blend_hex(base, self.spec.visuals.orb_head, min(1.0, 0.30 + effect_strength * 0.45))
        if effect == "harvest":
            return blend_hex("#FFD779", self.spec.visuals.playfield_overlay, 0.30 + effect_strength * 0.55)
        if color == "red" and intensity > 0:
            base = self.spec.visuals.red_levels[max(0, intensity - 1)]
        elif color == "green" and intensity > 0:
            base = self.spec.visuals.green_levels[max(0, intensity - 1)]
        else:
            base = self.spec.visuals.orb_head
        return blend_hex(base, self.spec.visuals.orb_head, min(1.0, 0.35 + effect_strength * 0.65))

    def _seed_flight_position(self, flight) -> tuple[float, float]:
        start = self.sim.topology.nodes[flight.start_node_id]
        target = self.sim.topology.nodes[flight.target_node_id]
        progress = 1.0 - (flight.time_remaining / flight.total_time if flight.total_time > 0 else 1.0)
        progress = min(1.0, max(0.0, progress))
        return (
            start.x + (target.x - start.x) * progress,
            start.y + (target.y - start.y) * progress,
        )

    def _orb_trail_length(self, orb: Orb) -> float:
        if orb.owner_tower_id == "power_tower":
            return self.spec.power_snake_tail_length
        tower = self.sim.towers.get(orb.owner_tower_id)
        if tower is None:
            return 0.0
        return self.spec.towers[tower.archetype].snake_tail_length

    def _runtime_spec_for_canvas(self) -> GameSpec:
        playfield_width = self.canvas.winfo_width()
        playfield_height = self.canvas.winfo_height()
        if playfield_width <= 1:
            playfield_width = self.canvas.winfo_reqwidth()
        if playfield_height <= 1:
            playfield_height = self.canvas.winfo_reqheight()
        return replace(self.spec, playfield_width=playfield_width, playfield_height=playfield_height)
