from __future__ import annotations

import gc
from dataclasses import replace
import math
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


_APP_HOST_ROOT: tk.Tk | None = None


def _host_root_alive(root: tk.Tk | None) -> bool:
    if root is None:
        return False
    try:
        return bool(root.winfo_exists())
    except tk.TclError:
        return False


def _acquire_app_root() -> tk.Tk:
    global _APP_HOST_ROOT
    if not _host_root_alive(_APP_HOST_ROOT):
        _APP_HOST_ROOT = tk.Tk()
        return _APP_HOST_ROOT
    try:
        for child in _APP_HOST_ROOT.winfo_children():
            child.destroy()
    except tk.TclError:
        pass
    try:
        _APP_HOST_ROOT.attributes("-fullscreen", False)
    except tk.TclError:
        pass
    try:
        _APP_HOST_ROOT.deiconify()
    except tk.TclError:
        pass
    return _APP_HOST_ROOT


class GridlineApp:
    def __init__(self, spec: GameSpec | None = None) -> None:
        self.spec = spec or load_game_spec()
        self.root = _acquire_app_root()
        self.root.title("Gridline MVP")
        self.root.geometry(f"{self.spec.width}x{self.spec.height}")
        self.root.configure(bg=self.spec.visuals.background)
        self.root.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.root.bind("<Destroy>", self._on_root_destroy, add="+")
        self.fullscreen = False
        self.rail_panel_bg = "#0E1824"
        self.rail_panel_alt_bg = "#101D2B"
        self.rail_panel_quiet_bg = "#0A1320"
        self.rail_panel_border = "#203447"
        self.rail_panel_border_strong = "#2F4F6B"
        self.rail_emphasis_bg = "#13283A"

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

        self.status_text = tk.StringVar(master=self.root)
        self.detail_text = tk.StringVar(master=self.root)
        self.feedback_text = tk.StringVar(master=self.root)
        self.upgrade_text = tk.StringVar(master=self.root)
        self.utility_hint_text = tk.StringVar(master=self.root)
        self.status_row_vars: dict[str, tk.StringVar] = {}
        self.status_row_labels: dict[str, tk.Label] = {}
        self.status_row_order = ("pressure", "phase", "corruption", "coins", "power", "level", "telemetry", "harvest", "surge", "status")
        self.action_buttons: dict[str, tk.Button] = {}
        self.utility_buttons: dict[str, tk.Button] = {}
        self.action_groups: dict[str, tk.Frame] = {}
        self.action_group_headers: dict[str, tk.Label] = {}
        self.action_group_keys: dict[str, list[str]] = {}
        self._last_action_selection_signature: tuple[str | None, str] | None = None
        self._last_detail_selection_signature: tuple[str | None, str] | None = None
        self._sidebar_rebalance_after_id: str | None = None
        self._action_scroll_reset_after_id: str | None = None
        self._detail_scroll_reset_after_id: str | None = None
        self._loop_after_id: str | None = None
        self._build_sidebar()
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.tick_ms = int(1000 / self.spec.simulation_tick_rate)
        self.sim_dt = 1.0 / self.spec.simulation_tick_rate
        self.sidebar_refresh_interval = 1.0 / max(1, self.spec.hud_refresh_rate)
        self.sidebar_refresh_elapsed = self.sidebar_refresh_interval
        self.loop_running = False
        self.root.update_idletasks()
        self.sim = GameSimulation(self._runtime_spec_for_canvas())
        self.shell_state = "title_ready"
        self.highest_power_funding = self.sim.power.funding_percent
        self.power_deploy_count = 0
        self.defeat_summary: dict[str, object] = {}
        self._reset_board_event_feedback()
        self._queue_sidebar_rebalance()
        self._render()
        self._refresh_sidebar()

    def _build_sidebar(self) -> None:
        label_style = {
            "bg": self.spec.visuals.sidebar,
            "fg": self.spec.visuals.text,
            "anchor": "w",
            "justify": "left",
        }
        self.sidebar.bind("<Configure>", self._on_sidebar_configure)
        self.title_label = tk.Label(self.sidebar, text="Gridline", font=("Consolas", 18, "bold"), **label_style)
        self.title_label.pack(fill=tk.X, padx=16, pady=(16, 8))

        self.status_frame, status_body = self._build_section_shell(self.sidebar, "Run Status", self.rail_panel_bg, self.rail_panel_border_strong)
        self.status_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        for key in self.status_row_order:
            var = tk.StringVar(master=self.root)
            label = tk.Label(
                status_body,
                textvariable=var,
                font=("Consolas", 10, "bold" if key in {"pressure", "phase", "corruption", "power"} else "normal"),
                bg=self.rail_emphasis_bg if key in {"pressure", "phase", "corruption", "power"} else self.rail_panel_bg,
                fg=self.spec.visuals.text if key in {"pressure", "phase", "corruption", "power"} else self.spec.visuals.muted_text,
                anchor="w",
                justify="left",
                padx=8,
                pady=4,
            )
            label.pack(fill=tk.X, pady=(0, 2))
            self.status_row_vars[key] = var
            self.status_row_labels[key] = label

        self.details_frame, detail_body_shell = self._build_section_shell(self.sidebar, "Selection", self.rail_panel_alt_bg, self.rail_panel_border)
        self.details_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.details_frame.pack_propagate(False)
        self.details_frame.configure(height=220)
        self.detail_body = tk.Frame(detail_body_shell, bg=self.rail_panel_alt_bg)
        self.detail_body.pack(fill=tk.BOTH, expand=True)
        self.detail_canvas = tk.Canvas(self.detail_body, bg=self.rail_panel_alt_bg, highlightthickness=0, bd=0)
        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.detail_scrollbar = tk.Scrollbar(self.detail_body, orient=tk.VERTICAL, command=self.detail_canvas.yview)
        self.detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_canvas.configure(yscrollcommand=self.detail_scrollbar.set)
        self.detail_inner = tk.Frame(self.detail_canvas, bg=self.rail_panel_alt_bg)
        self.detail_canvas_window = self.detail_canvas.create_window((0, 0), window=self.detail_inner, anchor="nw")
        self.detail_inner.bind("<Configure>", self._sync_detail_scrollregion)
        self.detail_canvas.bind("<Configure>", self._sync_detail_canvas_width)
        tk.Label(
            self.detail_inner,
            textvariable=self.detail_text,
            font=("Consolas", 10),
            wraplength=self.spec.visuals.sidebar_width - 32,
            bg=self.rail_panel_alt_bg,
            fg=self.spec.visuals.text,
            anchor="w",
            justify="left",
        ).pack(fill=tk.X)
        tk.Label(
            self.detail_inner,
            textvariable=self.feedback_text,
            font=("Consolas", 10),
            wraplength=self.spec.visuals.sidebar_width - 32,
            fg="#F2C46D",
            bg=self.rail_panel_alt_bg,
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, pady=(6, 0))
        tk.Label(
            self.detail_inner,
            textvariable=self.upgrade_text,
            font=("Consolas", 9),
            wraplength=self.spec.visuals.sidebar_width - 32,
            bg=self.rail_panel_alt_bg,
            fg=self.spec.visuals.muted_text,
            anchor="w",
            justify="left",
        ).pack(fill=tk.X, pady=(6, 0))

        self.actions_shell, action_body_shell = self._build_section_shell(self.sidebar, "Actions", self.rail_panel_bg, self.rail_panel_border)
        self.actions_shell.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self.action_canvas = tk.Canvas(action_body_shell, bg=self.rail_panel_bg, highlightthickness=0, bd=0)
        self.action_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.action_scrollbar = tk.Scrollbar(action_body_shell, orient=tk.VERTICAL, command=self.action_canvas.yview)
        self.action_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_canvas.configure(yscrollcommand=self.action_scrollbar.set)
        self.action_inner = tk.Frame(self.action_canvas, bg=self.rail_panel_bg)
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

        self.utility_frame, utility_body = self._build_section_shell(self.sidebar, "Utility", self.rail_panel_quiet_bg, self.rail_panel_border)
        self.utility_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 16))
        self.utility_note_label = tk.Label(
            utility_body,
            textvariable=self.utility_hint_text,
            font=("Consolas", 9),
            bg=self.rail_panel_quiet_bg,
            fg=self.spec.visuals.muted_text,
            anchor="w",
            justify="left",
            wraplength=self.spec.visuals.sidebar_width - 48,
        )
        self.utility_note_label.pack(fill=tk.X, pady=(0, 4))
        self.utility_buttons["start_run"] = self._make_shell_button(utility_body, "Start Run", self._start_run)
        self.utility_buttons["resume"] = self._make_shell_button(utility_body, "Resume", self._resume_run)
        self.utility_buttons["replay"] = self._make_shell_button(utility_body, "Replay", self._replay_run)
        self.utility_buttons["quit"] = self._make_shell_button(utility_body, "Quit", self._quit_app)

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
        group_frame = tk.Frame(
            self.action_inner,
            bg=self.rail_panel_alt_bg,
            highlightbackground=self.rail_panel_border,
            highlightthickness=1,
            bd=0,
        )
        header = self._section_label(group_frame, title)
        header.pack(fill=tk.X, padx=8, pady=(8, 4))
        button_shell = tk.Frame(group_frame, bg=self.rail_panel_alt_bg)
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

    def _make_shell_button(self, parent: tk.Widget, label: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=label,
            command=command,
            bg="#132235",
            fg=self.spec.visuals.text,
            activebackground="#1C3654",
            activeforeground=self.spec.visuals.text,
            relief=tk.FLAT,
            disabledforeground="#6F8195",
            anchor="w",
            justify="left",
            font=("Consolas", 10, "bold"),
            height=2,
            padx=10,
            pady=6,
        )

    def _section_label(self, parent: tk.Widget, text: str) -> tk.Label:
        parent_bg = str(parent.cget("bg"))
        return tk.Label(
            parent,
            text=text,
            font=("Consolas", 10, "bold"),
            bg=parent_bg,
            fg=self.spec.visuals.muted_text,
            anchor="w",
            justify="left",
        )

    def _build_section_shell(self, parent: tk.Widget, title: str, bg_color: str, border_color: str) -> tuple[tk.Frame, tk.Frame]:
        shell = tk.Frame(parent, bg=bg_color, highlightbackground=border_color, highlightthickness=1, bd=0)
        self._section_label(shell, title).pack(fill=tk.X, padx=10, pady=(8, 6))
        body = tk.Frame(shell, bg=bg_color)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        return shell, body

    def _sync_action_scrollregion(self, _event=None) -> None:
        self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all"))

    def _sync_action_canvas_width(self, event) -> None:
        self.action_canvas.itemconfigure(self.action_canvas_window, width=event.width)

    def _sync_detail_scrollregion(self, _event=None) -> None:
        self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def _sync_detail_canvas_width(self, event) -> None:
        self.detail_canvas.itemconfigure(self.detail_canvas_window, width=event.width)

    def _on_sidebar_configure(self, _event=None) -> None:
        self._queue_sidebar_rebalance()

    def _queue_sidebar_rebalance(self) -> None:
        if self._sidebar_rebalance_after_id is not None:
            self.root.after_cancel(self._sidebar_rebalance_after_id)
        self._sidebar_rebalance_after_id = self.root.after_idle(self._rebalance_sidebar_layout)

    def _on_root_destroy(self, event) -> None:
        if event.widget is not self.root:
            return
        self._cleanup_root_callbacks()
        if getattr(tk, "_default_root", None) is self.root:
            tk._default_root = None

    def _cleanup_root_callbacks(self) -> None:
        if self._sidebar_rebalance_after_id is not None:
            try:
                self.root.after_cancel(self._sidebar_rebalance_after_id)
            except tk.TclError:
                pass
            self._sidebar_rebalance_after_id = None
        if self._loop_after_id is not None:
            try:
                self.root.after_cancel(self._loop_after_id)
            except tk.TclError:
                pass
            self._loop_after_id = None
        if self._action_scroll_reset_after_id is not None:
            try:
                self.action_canvas.after_cancel(self._action_scroll_reset_after_id)
            except tk.TclError:
                pass
            self._action_scroll_reset_after_id = None
        if self._detail_scroll_reset_after_id is not None:
            try:
                self.detail_canvas.after_cancel(self._detail_scroll_reset_after_id)
            except tk.TclError:
                pass
            self._detail_scroll_reset_after_id = None
        self.loop_running = False

    def _rebalance_sidebar_layout(self) -> None:
        self._sidebar_rebalance_after_id = None
        shell_state = getattr(self, "shell_state", "title_ready")
        sidebar_height = self.sidebar.winfo_height()
        if sidebar_height <= 1:
            return
        title_height = max(self.title_label.winfo_height(), self.title_label.winfo_reqheight())
        status_height = max(self.status_frame.winfo_height(), self.status_frame.winfo_reqheight())
        utility_height = 0
        if self.utility_frame.winfo_manager():
            utility_height = max(self.utility_frame.winfo_height(), self.utility_frame.winfo_reqheight())
        fixed_height = title_height + status_height + utility_height + 56
        remaining = max(180, sidebar_height - fixed_height)
        if shell_state == "active_run":
            action_floor = 260
            min_action_height = 220
            detail_floor = 48
            detail_min = 72
            detail_max = 104
        else:
            action_floor = 208
            min_action_height = 156
            detail_floor = 72
            detail_min = 104
            detail_max = 220
        detail_req = self.detail_inner.winfo_reqheight() + 28
        detail_height = min(detail_max, max(detail_min, min(detail_req, remaining - action_floor)))
        action_height = remaining - detail_height
        if action_height < min_action_height:
            detail_height = max(detail_floor, remaining - min_action_height)
            action_height = remaining - detail_height
        self.details_frame.configure(height=detail_height)
        self.detail_canvas.configure(height=max(36, detail_height - 24))
        min_canvas_height = 140 if shell_state == "active_run" else 156
        self.action_canvas.configure(height=max(min_canvas_height, action_height))

    def _toggle_fullscreen(self, _event=None) -> None:
        if not self.spec.fullscreen_toggle_enabled:
            return
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        self._queue_sidebar_rebalance()

    def _on_canvas_click(self, event) -> None:
        if self.shell_state != "active_run":
            return
        self.sim.click_world(event.x, event.y)
        self._refresh_sidebar()

    def _reset_run(self) -> None:
        self._cancel_scheduled_loop()
        self.root.update_idletasks()
        self.sim = GameSimulation(self._runtime_spec_for_canvas())
        self.highest_power_funding = self.sim.power.funding_percent
        self.power_deploy_count = 0
        self.defeat_summary = {}
        self._reset_board_event_feedback()
        self.feedback_text.set("")
        self._last_action_selection_signature = None
        self._last_detail_selection_signature = None
        self.sidebar_refresh_elapsed = self.sidebar_refresh_interval

    def _start_run(self) -> None:
        self._reset_run()
        self.shell_state = "active_run"
        self._render()
        self._refresh_sidebar()
        self._schedule_loop()

    def _replay_run(self) -> None:
        self._start_run()

    def _resume_run(self) -> None:
        if self.sim.game_over:
            self._transition_to_defeat()
            return
        self.shell_state = "active_run"
        self._render()
        self._refresh_sidebar()
        self._schedule_loop()

    def _pause_run(self) -> None:
        if self.shell_state != "active_run":
            return
        self._cancel_scheduled_loop()
        self.shell_state = "paused"
        self._render()
        self._refresh_sidebar()

    def _quit_app(self) -> None:
        root = self.root
        if root is None:
            return
        try:
            root.update_idletasks()
        except tk.TclError:
            pass
        try:
            root.quit()
        except tk.TclError:
            pass
        self._cleanup_root_callbacks()
        try:
            root.unbind("<Escape>")
            root.unbind("<F11>")
            root.unbind("<Destroy>")
        except tk.TclError:
            pass
        try:
            for child in root.winfo_children():
                child.destroy()
        except tk.TclError:
            pass
        try:
            root.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        try:
            root.withdraw()
        except tk.TclError:
            pass
        self._release_tk_references()

    def _release_tk_references(self) -> None:
        for key, value in list(self.__dict__.items()):
            if isinstance(value, dict):
                value.clear()
                continue
            if isinstance(value, (tk.Variable, tk.Misc)):
                self.__dict__[key] = None
        gc.collect()

    def _on_escape(self, _event=None) -> None:
        if self.shell_state == "active_run":
            if self.sim.game_over:
                self._transition_to_defeat()
                return
            self._pause_run()
        elif self.shell_state == "paused":
            self._resume_run()

    def _schedule_loop(self) -> None:
        if self.shell_state != "active_run" or self._loop_after_id is not None:
            return
        self.loop_running = True
        self._loop_after_id = self.root.after(self.tick_ms, self._loop)

    def _cancel_scheduled_loop(self) -> None:
        if self._loop_after_id is not None:
            self.root.after_cancel(self._loop_after_id)
            self._loop_after_id = None
        self.loop_running = False

    def _transition_to_defeat(self) -> None:
        self._cancel_scheduled_loop()
        self.shell_state = "defeat_summary"
        self.defeat_summary = {
            "cause_of_loss": "Corruption threshold exceeded",
            "run_duration": self.sim.run_time,
            "highest_phase_reached": self.sim.phase_label(self.sim.highest_phase_reached),
            "corruption_percent_at_loss": self.sim.corruption_percent(),
            "highest_power_funding": self.highest_power_funding,
            "power_deploy_count": self.power_deploy_count,
        }
        self._render()
        self._refresh_sidebar()

    def run(self) -> None:
        self.root.mainloop()

    def _loop(self) -> None:
        self._loop_after_id = None
        if self.shell_state != "active_run":
            self.loop_running = False
            return
        previous_active_power = self.sim.power.active_hardpoint_id
        previous_surge_active = self.sim.surge_time_remaining > 0
        previous_clean_impacts = self._current_clean_impact_snapshot()
        self.sim.update(self.sim_dt)
        self._track_run_metrics(previous_active_power)
        self._update_board_event_feedback(self.sim_dt, previous_surge_active, previous_clean_impacts)
        if self.sim.game_over:
            self._transition_to_defeat()
            return
        self._render()
        self.sidebar_refresh_elapsed += self.sim_dt
        if self.sidebar_refresh_elapsed >= self.sidebar_refresh_interval:
            self._refresh_sidebar()
            self.sidebar_refresh_elapsed = 0.0
        self._schedule_loop()

    def _track_run_metrics(self, previous_active_power: str | None) -> None:
        self.highest_power_funding = max(self.highest_power_funding, self.sim.power.funding_percent)
        if previous_active_power is None and self.sim.power.active_hardpoint_id is not None:
            self.power_deploy_count += 1

    def _reset_board_event_feedback(self) -> None:
        self._surge_start_time_remaining = 0.0
        self._surge_end_fade_time_remaining = 0.0
        self._surge_pulse_elapsed = 0.0
        self._clean_feedback_events: dict[str, dict[str, float]] = {}

    def _current_clean_impact_snapshot(self) -> dict[str, float]:
        return {
            segment_id: impact.time_remaining
            for segment_id, impact in self.sim.segment_impacts.items()
            if impact.effect == "clean"
        }

    def _update_board_event_feedback(
        self,
        dt: float,
        previous_surge_active: bool,
        previous_clean_impacts: dict[str, float],
    ) -> None:
        surge_active = self.sim.surge_time_remaining > 0
        self._surge_pulse_elapsed = (self._surge_pulse_elapsed + dt) % 1.10
        if surge_active and not previous_surge_active:
            self._surge_start_time_remaining = 0.65
            self._surge_end_fade_time_remaining = 0.0
        elif previous_surge_active and not surge_active:
            self._surge_end_fade_time_remaining = 0.25
        if self._surge_start_time_remaining > 0:
            self._surge_start_time_remaining = max(0.0, self._surge_start_time_remaining - dt)
        if not surge_active and self._surge_end_fade_time_remaining > 0:
            self._surge_end_fade_time_remaining = max(0.0, self._surge_end_fade_time_remaining - dt)

        current_clean_impacts = self._current_clean_impact_snapshot()
        for segment_id, time_remaining in current_clean_impacts.items():
            previous_time = previous_clean_impacts.get(segment_id)
            if previous_time is None or time_remaining > previous_time + 1e-6:
                state = self.sim.segment_states[segment_id]
                self._clean_feedback_events[segment_id] = {
                    "sweep": 0.30,
                    "afterglow": 0.40,
                    "strength": 1.0 if state.color == "blue" else 0.8,
                }
        for segment_id in list(self._clean_feedback_events):
            event = self._clean_feedback_events[segment_id]
            if event["sweep"] > 0:
                event["sweep"] = max(0.0, event["sweep"] - dt)
            elif event["afterglow"] > 0:
                event["afterglow"] = max(0.0, event["afterglow"] - dt)
            else:
                self._clean_feedback_events.pop(segment_id, None)

    def _refresh_sidebar(self) -> None:
        hud = self.sim.hud_snapshot()
        recent_harvest = hud["recent_harvest_event"]
        status_line = {
            "title_ready": "Status: ready",
            "active_run": "Status: GAME OVER" if hud["game_over"] else "Status: running",
            "paused": "Status: paused",
            "defeat_summary": "Status: defeat summary",
        }[self.shell_state]
        status_rows = [
            ("pressure", f"Pressure: {self._pressure_badge(hud)}"),
            ("phase", f"Phase: {self._phase_status_text(hud)}"),
            ("corruption", f"Corruption: {self._meter_bar(hud['corruption_percent'], hud['failure_threshold'])} {hud['corruption_percent']:.1f}% / {hud['failure_threshold']:.0f}%"),
            ("coins", f"Coins: {hud['coins']}"),
            ("power", f"Power: {self._power_status_text(hud)}"),
            ("level", f"Level: {hud['level']}  Next: {hud['level_time_remaining']:.1f}s  Orbs: {hud['active_orb_count']}  Shots/s: {hud['shots_recent']}"),
            ("harvest", f"Harvest: {self._recent_harvest_text(recent_harvest)}"),
            ("surge", f"Surge: {'ACTIVE' if hud['surge_active'] else 'idle'}"),
            ("status", status_line),
        ]
        self.status_text.set("\n".join(text for _key, text in status_rows))
        self._update_status_rows(status_rows, hud)
        self.utility_hint_text.set(self._utility_hint())
        hardpoint = self.sim.selected_hardpoint()
        if hardpoint is None:
            if self.shell_state == "title_ready":
                self.detail_text.set("Run ready. Use Start Run to enter live play.")
            elif self.shell_state == "paused":
                self.detail_text.set("Simulation paused. Resume to restore live commands.")
            elif self.shell_state == "defeat_summary":
                self.detail_text.set(self._defeat_summary_text())
            else:
                self.detail_text.set("Select a hardpoint on the perimeter to build, upgrade, or deploy power.")
            self.upgrade_text.set("")
            self._update_button_states(hud["selected_object"], hud["action_availability"])
            self._maybe_reset_sidebar_scrolls(hud["selected_object"])
            self._refresh_utility_buttons()
            self._queue_sidebar_rebalance()
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
        if self.shell_state == "paused":
            lines.append("")
            lines.append("Simulation paused. Resume to restore live commands.")
        elif self.shell_state == "defeat_summary":
            lines.extend(["", self._defeat_summary_text()])
        self.detail_text.set("\n".join(lines))
        self.upgrade_text.set("\n".join(hud["upgrade_preview"]))
        self._update_button_states(hud["selected_object"], hud["action_availability"])
        self._maybe_reset_sidebar_scrolls(selected)
        self._refresh_utility_buttons()
        self._queue_sidebar_rebalance()

    def _update_status_rows(self, status_rows: list[tuple[str, str]], hud: dict[str, object]) -> None:
        emphasis_keys = {"pressure", "phase", "corruption", "power"}
        danger_keys = set()
        visible_by_state = {
            "title_ready": {"pressure", "phase", "corruption", "coins", "power", "status"},
            "active_run": {"pressure", "phase", "corruption", "coins", "power", "level"},
            "paused": {"pressure", "phase", "corruption", "power", "level", "surge", "status"},
            "defeat_summary": {"pressure", "phase", "corruption", "power", "status"},
        }
        visible_keys = set(visible_by_state[self.shell_state])
        if self.shell_state == "active_run":
            if hud["recent_harvest_event"] is not None:
                visible_keys.add("harvest")
            if hud["surge_active"]:
                visible_keys.add("surge")
        if "[CRITICAL]" in self._pressure_badge(hud) or hud["game_over"]:
            danger_keys.update({"pressure", "corruption"})
        if hud["surge_active"]:
            danger_keys.add("surge")
        if "[CRITICAL]" in hud["active_phase_badge"]:
            danger_keys.add("phase")
        if self.sim.power.active_hardpoint_id is not None or hud["power_charged"]:
            danger_keys.add("power")
        for key, text in status_rows:
            self.status_row_vars[key].set(text)
            bg = self.rail_emphasis_bg if key in emphasis_keys else self.rail_panel_bg
            fg = self.spec.visuals.text if key in emphasis_keys else self.spec.visuals.muted_text
            if key in danger_keys:
                bg = "#1A2332"
                fg = self.spec.visuals.warning if key == "surge" else self.spec.visuals.text
                if key in {"pressure", "corruption", "phase"} and (hud["game_over"] or "[CRITICAL]" in text):
                    fg = self.spec.visuals.critical
            self.status_row_labels[key].configure(bg=bg, fg=fg)
        for key in self.status_row_order:
            label = self.status_row_labels[key]
            if label.winfo_manager():
                label.pack_forget()
        for key in self.status_row_order:
            if key in visible_keys:
                self.status_row_labels[key].pack(fill=tk.X, pady=(0, 2))

    def _utility_hint(self) -> str:
        if self.shell_state == "active_run":
            return "Low-frequency session controls stay quiet here. Esc pauses. F11 toggles fullscreen."
        if self.shell_state == "title_ready":
            return "Start Run begins the session. F11 toggles fullscreen."
        if self.shell_state == "paused":
            return "Session controls are live here. Resume returns to the frozen board context."
        return "Replay is the primary recovery action. Quit remains available as a secondary session control."

    def _update_button_states(self, selected: dict[str, object], availability: dict[str, tuple[bool, str]]) -> None:
        context = selected.get("kind", "none")
        self._update_context_action_labels(selected, availability)
        self._sync_utility_region()
        if self.shell_state != "active_run":
            self._set_visible_action_groups(())
            for header in self.action_group_headers.values():
                header.configure(fg=self.spec.visuals.muted_text)
            for button in self.action_buttons.values():
                button.configure(state=tk.DISABLED)
            return
        tower = selected.get("tower")
        active_groups: tuple[str, ...] = ("power",)
        if context in {"none", "empty"}:
            active_groups = ("build", "power")
        elif context == "tower":
            active_groups = ("tower", "power")
            if tower is not None and tower.archetype == "seed_tower":
                active_groups = ("tower", "seed", "power")
        elif context == "power":
            active_groups = ("power",)

        self._set_visible_action_groups(active_groups)

        for group_key, header in self.action_group_headers.items():
            header.configure(fg=self.spec.visuals.text if group_key in active_groups else self.spec.visuals.muted_text)

        for key, button in self.action_buttons.items():
            enabled, _reason = availability.get(key, (True, ""))
            button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def _refresh_utility_buttons(self) -> None:
        visible_by_state = {
            "title_ready": ("start_run", "quit"),
            "active_run": (),
            "paused": ("resume", "replay", "quit"),
            "defeat_summary": ("replay", "quit"),
        }
        visible = set(visible_by_state[self.shell_state])
        primary_key = None if self.shell_state == "active_run" else self._shell_presentation()["primary_action_key"]
        for key, button in self.utility_buttons.items():
            if key in visible:
                if button.winfo_manager() != "pack":
                    button.pack(fill=tk.X, pady=3)
                button.configure(state=tk.NORMAL)
                self._style_shell_button(button, is_primary=key == primary_key)
            elif button.winfo_manager():
                button.pack_forget()

    def _sync_utility_region(self) -> None:
        if self.shell_state == "active_run":
            if self.utility_frame.winfo_manager():
                self.utility_frame.pack_forget()
            return
        if self.utility_frame.winfo_manager() != "pack":
            self.utility_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(0, 16))

    def _set_visible_action_groups(self, visible_groups: tuple[str, ...]) -> None:
        for group_frame in self.action_groups.values():
            if group_frame.winfo_manager():
                group_frame.pack_forget()
        for group_key in visible_groups:
            self.action_groups[group_key].pack(fill=tk.X, pady=(0, 10))

    def _style_shell_button(self, button: tk.Button, is_primary: bool) -> None:
        if is_primary:
            button.configure(
                bg="#245985",
                fg="#F4FBFF",
                activebackground="#2F6E9F",
                activeforeground="#F4FBFF",
                font=("Consolas", 10, "bold"),
            )
        else:
            button.configure(
                bg="#132235",
                fg=self.spec.visuals.text,
                activebackground="#1C3654",
                activeforeground=self.spec.visuals.text,
                font=("Consolas", 10, "bold"),
            )

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
            f"+{recent_harvest['amount']}c | {recent_harvest['tower_name']} | "
            f"{recent_harvest['mode_name']} | {recent_harvest['age']:.1f}s ago"
        )

    def _maybe_reset_sidebar_scrolls(self, selected: dict[str, object]) -> None:
        selection_signature = (self.sim.selected_hardpoint_id, str(selected.get("kind", "none")))
        if selection_signature == self._last_action_selection_signature:
            return
        self._last_action_selection_signature = selection_signature
        if self._action_scroll_reset_after_id is not None:
            self.action_canvas.after_cancel(self._action_scroll_reset_after_id)
        self._action_scroll_reset_after_id = self.action_canvas.after_idle(self._reset_action_scroll)
        self._last_detail_selection_signature = selection_signature
        if self._detail_scroll_reset_after_id is not None:
            self.detail_canvas.after_cancel(self._detail_scroll_reset_after_id)
        self._detail_scroll_reset_after_id = self.detail_canvas.after_idle(self._reset_detail_scroll)

    def _reset_action_scroll(self) -> None:
        self._action_scroll_reset_after_id = None
        self.action_canvas.yview_moveto(0.0)

    def _reset_detail_scroll(self) -> None:
        self._detail_scroll_reset_after_id = None
        self.detail_canvas.yview_moveto(0.0)

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

    def _shell_presentation(self) -> dict[str, object]:
        return {
            "title_ready": {
                "badge": "READY SHELL",
                "title": "GRIDLINE READY",
                "subhead": "Command rail armed. The board is loaded and waiting on your first deployment order.",
                "primary_action_key": "start_run",
                "primary_action_label": "Start Run",
                "secondary_actions": ("Quit", "F11 Fullscreen"),
                "accent": "#8BD3FF",
                "panel_fill": "#09131E",
                "scrim_fill": "#07111A",
                "scrim_stipple": "gray50",
            },
            "paused": {
                "badge": "PAUSE SHELL",
                "title": "RUN PAUSED",
                "subhead": "Simulation time is frozen. Board state and the current selection are preserved exactly for resume.",
                "primary_action_key": "resume",
                "primary_action_label": "Resume",
                "secondary_actions": ("Replay", "Quit", "Esc Resume", "F11 Fullscreen"),
                "accent": "#F2C46D",
                "panel_fill": "#09131E",
                "scrim_fill": "#02060A",
                "scrim_stipple": "gray25",
            },
            "defeat_summary": {
                "badge": "DEFEAT SHELL",
                "title": "GRID FAILURE",
                "subhead": "The run has resolved. Review the loss summary, then replay immediately or step away from the session.",
                "primary_action_key": "replay",
                "primary_action_label": "Replay",
                "secondary_actions": ("Quit", "F11 Fullscreen"),
                "accent": self.spec.visuals.critical,
                "panel_fill": "#110B10",
                "scrim_fill": "#02060A",
                "scrim_stipple": "gray25",
            },
        }[self.shell_state]

    def _defeat_summary_rows(self) -> list[str]:
        if not self.defeat_summary:
            return [
                "Cause of loss: Run lost",
                "Run duration: 0.0s",
                "Highest phase reached: Opening Containment",
                "Corruption at loss: 0.0%",
                "Power usage: 0% peak funding, 0 deploys",
            ]
        return [
            f"Cause of loss: {self.defeat_summary['cause_of_loss']}",
            f"Run duration: {self.defeat_summary['run_duration']:.1f}s",
            f"Highest phase reached: {self.defeat_summary['highest_phase_reached']}",
            f"Corruption at loss: {self.defeat_summary['corruption_percent_at_loss']:.1f}%",
            f"Power usage: {self.defeat_summary['highest_power_funding']}% peak funding, {self.defeat_summary['power_deploy_count']} deploys",
        ]

    def _defeat_summary_text(self) -> str:
        return "\n".join(self._defeat_summary_rows())

    def _phase_status_text(self, hud: dict[str, object]) -> str:
        phase_transition = hud["phase_transition"]
        if phase_transition is not None:
            return f"[SHIFT] [{hud['active_phase_badge']}] {hud['active_phase_label']}"
        return f"[{hud['active_phase_badge']}] {hud['active_phase_label']}"

    def _phase_accent(self, phase_id: str) -> str:
        return {
            "opening_containment": "#8BD3FF",
            "escalation": "#F2C46D",
            "critical_load": self.spec.visuals.critical,
        }[phase_id]

    def _render(self) -> None:
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        outer_margin_fill = blend_hex(self.spec.visuals.background, "#010306", 0.62)
        self.canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill=outer_margin_fill, outline="")
        board_left, board_top, board_right, board_bottom = self.sim.topology.playfield_rect
        board_fill = blend_hex(self.spec.visuals.playfield_overlay, self.spec.visuals.background, 0.92)
        board_frame = blend_hex(self.spec.visuals.neutral_large, self.spec.visuals.background, 0.18)
        board_inset = blend_hex(self.spec.visuals.neutral_medium, self.spec.visuals.playfield_overlay, 0.42)
        self.canvas.create_rectangle(
            board_left,
            board_top,
            board_right,
            board_bottom,
            fill=board_fill,
            outline=board_frame,
            width=2,
            tags=("board_surface",),
        )
        self.canvas.create_rectangle(
            board_left + 3,
            board_top + 3,
            board_right - 3,
            board_bottom - 3,
            fill="",
            outline=board_inset,
            width=1,
            tags=("board_inset",),
        )
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

        self._render_board_event_feedback()

        self.canvas.create_text(16, 16, anchor="nw", fill=self.spec.visuals.text, font=("Consolas", 12, "bold"), text=f"Coins {self.sim.coins}   Corruption {self.sim.corruption_percent():.1f}%   Orbs {len(self.sim.orbs)}   Enemies {len(self.sim.enemies)}")
        if self.sim.surge_time_remaining > 0:
            self.canvas.create_text(16, 36, anchor="nw", fill=self.spec.visuals.warning, font=("Consolas", 11, "bold"), text=f"SURGE ACTIVE {self.sim.surge_time_remaining:.1f}s")
        self._render_phase_banner()
        if self.shell_state == "active_run" and self.sim.game_over:
            self.canvas.create_text(self.canvas.winfo_width() / 2, 36, fill=self.spec.visuals.critical, font=("Consolas", 16, "bold"), text="GRID FAILURE")
        self._render_shell_overlay(canvas_width, canvas_height)

    def _render_phase_banner(self) -> None:
        if self.shell_state != "active_run":
            return
        phase_transition = self.sim.phase_transition_snapshot()
        if phase_transition is None:
            return
        board_left, board_top, board_right, _board_bottom = self.sim.topology.playfield_rect
        center_x = (board_left + board_right) / 2
        banner_width = min(360, board_right - board_left - 80)
        banner_height = 42
        left = center_x - banner_width / 2
        top = board_top + 14
        right = center_x + banner_width / 2
        bottom = top + banner_height
        accent = self._phase_accent(str(phase_transition["phase_id"]))
        self.canvas.create_rectangle(left, top, right, bottom, fill="#0A1622", outline=accent, width=2, tags=("phase_banner",))
        self.canvas.create_text(
            left + 16,
            top + 12,
            anchor="nw",
            fill=accent,
            font=("Consolas", 9, "bold"),
            text=f"{phase_transition['badge']} // {phase_transition['label']}",
            tags=("phase_banner",),
        )
        self.canvas.create_text(
            center_x,
            top + 28,
            anchor="center",
            fill=self.spec.visuals.text,
            font=("Consolas", 9),
            text=str(phase_transition["banner_text"]),
            tags=("phase_banner",),
        )

    def _render_board_event_feedback(self) -> None:
        if self.shell_state not in {"active_run", "paused", "defeat_summary"}:
            return
        self._render_surge_feedback()
        self._render_clean_feedback()

    def _render_surge_feedback(self) -> None:
        surge_active = self.sim.surge_time_remaining > 0
        if not surge_active and self._surge_start_time_remaining <= 0 and self._surge_end_fade_time_remaining <= 0:
            return
        board_left, board_top, board_right, board_bottom = self.sim.topology.playfield_rect
        pulse_phase = self._surge_pulse_elapsed / 1.10
        pulse_wave = 1.0 - abs(1.0 - (pulse_phase * 2.0))
        persistent_strength = 0.0
        if surge_active:
            persistent_strength = 0.20 + pulse_wave * 0.28
        elif self._surge_end_fade_time_remaining > 0:
            persistent_strength = 0.26 * (self._surge_end_fade_time_remaining / 0.25)
        if persistent_strength > 0:
            color = blend_hex("#F2C46D", self.spec.visuals.background, 0.30 + persistent_strength)
            width = 1.5 + persistent_strength * 1.8
            corner = 26 + pulse_wave * 8
            offset = 6
            corners = (
                (board_left - offset, board_top - offset, 1, 1),
                (board_right + offset, board_top - offset, -1, 1),
                (board_left - offset, board_bottom + offset, 1, -1),
                (board_right + offset, board_bottom + offset, -1, -1),
            )
            for x, y, dx, dy in corners:
                self.canvas.create_line(x, y, x + dx * corner, y, fill=color, width=width, capstyle=tk.ROUND, tags=("board_event_feedback", "surge_feedback"))
                self.canvas.create_line(x, y, x, y + dy * corner, fill=color, width=width, capstyle=tk.ROUND, tags=("board_event_feedback", "surge_feedback"))
        if self._surge_start_time_remaining > 0:
            start_strength = self._surge_start_time_remaining / 0.65
            color = blend_hex("#FFD36A", self.spec.visuals.background, 0.25 + start_strength * 0.70)
            self.canvas.create_rectangle(
                board_left - 8,
                board_top - 8,
                board_right + 8,
                board_bottom + 8,
                outline=color,
                width=2.0 + start_strength * 2.0,
                tags=("board_event_feedback", "surge_feedback"),
            )

    def _render_clean_feedback(self) -> None:
        for segment_id, event in self._clean_feedback_events.items():
            if event["sweep"] > 0:
                ratio = event["sweep"] / 0.30
                glow_strength = event["strength"] * (0.45 + ratio * 0.55)
                core_strength = event["strength"] * (0.35 + ratio * 0.45)
                bleed = 4.0 + ratio * 4.0
            else:
                ratio = event["afterglow"] / 0.40
                glow_strength = event["strength"] * ratio * 0.38
                core_strength = event["strength"] * ratio * 0.22
                bleed = 3.0
            x1, y1, x2, y2 = self._segment_endpoints_with_bleed(segment_id, bleed)
            glow_color = blend_hex("#9FE8FF", self.spec.visuals.playfield_overlay, 0.22 + min(1.0, glow_strength) * 0.70)
            core_color = blend_hex("#6FD7FF", self.spec.visuals.playfield_overlay, 0.18 + min(1.0, core_strength) * 0.72)
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=glow_color,
                width=3.0 + glow_strength * 4.0,
                capstyle=tk.ROUND,
                tags=("board_event_feedback", "clean_feedback"),
            )
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=core_color,
                width=1.2 + core_strength * 2.2,
                capstyle=tk.ROUND,
                tags=("board_event_feedback", "clean_feedback"),
            )

    def _segment_endpoints_with_bleed(self, segment_id: str, bleed: float) -> tuple[float, float, float, float]:
        segment = self.sim.topology.segments[segment_id]
        a = self.sim.topology.nodes[segment.a]
        b = self.sim.topology.nodes[segment.b]
        dx = b.x - a.x
        dy = b.y - a.y
        length = max(1.0, math.hypot(dx, dy))
        ux = dx / length
        uy = dy / length
        return (
            a.x - ux * bleed,
            a.y - uy * bleed,
            b.x + ux * bleed,
            b.y + uy * bleed,
        )

    def _render_shell_overlay(self, canvas_width: int, canvas_height: int) -> None:
        if self.shell_state == "active_run":
            return
        presentation = self._shell_presentation()
        overlay_width = min(440, max(320, canvas_width - 120))
        overlay_height = 250 if self.shell_state == "defeat_summary" else 196
        left = (canvas_width - overlay_width) / 2
        top = (canvas_height - overlay_height) / 2
        right = left + overlay_width
        bottom = top + overlay_height
        border = blend_hex(self.spec.visuals.neutral_large, self.spec.visuals.background, 0.35)
        accent = str(presentation["accent"])
        self.canvas.create_rectangle(
            0,
            0,
            canvas_width,
            canvas_height,
            fill=str(presentation["scrim_fill"]),
            outline="",
            stipple=str(presentation["scrim_stipple"]),
            tags=("shell_overlay", "shell_scrim"),
        )
        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=str(presentation["panel_fill"]),
            outline=border,
            width=2,
            tags=("shell_overlay",),
        )
        self.canvas.create_rectangle(left, top, right, top + 8, fill=accent, outline="", tags=("shell_overlay",))
        self.canvas.create_text(
            left + 24,
            top + 24,
            anchor="nw",
            fill=blend_hex(accent, self.spec.visuals.background, 0.15),
            font=("Consolas", 9, "bold"),
            text=str(presentation["badge"]),
            tags=("shell_overlay",),
        )
        self.canvas.create_text(
            left + 24,
            top + 48,
            anchor="nw",
            fill=self.spec.visuals.text,
            font=("Consolas", 18, "bold"),
            text=str(presentation["title"]),
            tags=("shell_overlay",),
        )
        self.canvas.create_text(
            left + 24,
            top + 82,
            anchor="nw",
            width=overlay_width - 48,
            fill=self.spec.visuals.muted_text,
            font=("Consolas", 10),
            justify="left",
            text=str(presentation["subhead"]),
            tags=("shell_overlay",),
        )
        primary_label = f"PRIMARY // {presentation['primary_action_label']}"
        secondary_label = "AUX // " + "   ".join(str(label) for label in presentation["secondary_actions"])
        self.canvas.create_rectangle(left + 24, bottom - 60, left + 186, bottom - 28, fill=accent, outline="", tags=("shell_overlay",))
        self.canvas.create_text(
            left + 36,
            bottom - 44,
            anchor="w",
            fill="#03111A",
            font=("Consolas", 10, "bold"),
            text=primary_label,
            tags=("shell_overlay",),
        )
        self.canvas.create_text(
            left + 24,
            bottom - 16,
            anchor="sw",
            width=overlay_width - 48,
            fill=self.spec.visuals.muted_text,
            font=("Consolas", 9),
            justify="left",
            text=secondary_label,
            tags=("shell_overlay",),
        )
        if self.shell_state == "defeat_summary":
            summary_top = top + 126
            for index, row in enumerate(self._defeat_summary_rows()):
                self.canvas.create_text(
                    left + 24,
                    summary_top + index * 22,
                    anchor="nw",
                    width=overlay_width - 48,
                    fill=self.spec.visuals.text if index == 0 else self.spec.visuals.muted_text,
                    font=("Consolas", 10, "bold" if index == 0 else "normal"),
                    justify="left",
                    text=row,
                    tags=("shell_overlay",),
                )

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
