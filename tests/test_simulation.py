from dataclasses import replace

from gridline.app import blend_hex, build_faded_trail_segments, build_orb_trail_points, enemy_render_color
from gridline.simulation import GameSimulation, Orb
from gridline.app import GridlineApp
from gridline.spec import default_spec, load_game_spec
from gridline.topology import build_topology


def test_corruption_formula_is_bounded():
    sim = GameSimulation(default_spec())
    value = sim.corruption_percent()
    assert 0.0 <= value <= 100.0


def test_hardpoint_builds_directly_without_activation():
    sim = GameSimulation(default_spec())
    assert len(sim.hardpoints) == 12
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    assert sim.build_tower("basic_tower")
    assert first.tower is not None


def test_seed_mode_purchase_and_swap():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("seed_tower")
    tower = first.tower
    assert tower is not None
    sim.coins = 999
    assert sim.purchase_secondary_mode()
    assert sim.toggle_selected_mode()
    assert tower.active_mode == "secondary"


def test_game_config_overrides_runtime_spec():
    spec = load_game_spec("game_config.json")
    assert spec.width == 1280
    assert spec.height == 720
    assert spec.starting_coins == 339
    assert spec.hardpoint_count == 12
    assert spec.level_interval == 45
    assert spec.simulation_tick_rate == 60
    assert spec.hud_refresh_rate == 10
    assert spec.spread_interval == 24
    assert spec.green_spread_interval == 10
    assert spec.green_spread_chance_by_tier == {"large": 0.13, "medium": 0.115, "small": 0.095}
    assert spec.harvest_income_green == (10, 18, 30)
    assert spec.power_funding_chunk_cost == 34
    assert spec.power_duration == 6
    assert spec.towers["basic_tower"].build_cost == 26
    assert spec.towers["seed_tower"].shot_range == 340
    assert spec.towers["basic_tower"].secondary_mode.purchase_cost == 10
    assert spec.towers["seed_tower"].secondary_mode.fire_rate_multiplier == 2.2
    assert spec.towers["burst_tower"].secondary_mode.shot_cost_multiplier == 0.25
    assert spec.enemies["tower_striker"].hp == 25
    assert spec.enemies["corruption_seeder"].hp == 18
    assert spec.spawn_interval_floor == 3.2
    assert abs(spec.base_spawn_interval - 4.8) < 1e-9
    assert spec.spawn_rate_growth_per_level == 0.02
    assert spec.visuals.neutral_large != spec.visuals.neutral_medium
    assert spec.visuals.neutral_medium != spec.visuals.neutral_small
    assert spec.visuals.large_line_width > spec.visuals.medium_line_width > spec.visuals.small_line_width
    assert spec.visuals.red_levels[0] != spec.visuals.red_levels[2]
    assert spec.visuals.green_levels[0] != spec.visuals.green_levels[2]


def test_seed_tower_uses_delayed_flight_before_orb_release():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("seed_tower")
    tower = first.tower
    assert tower is not None
    sim._attempt_fire_tower(tower)
    assert len(sim.seed_flights) >= 1
    assert len(sim.orbs) == 0
    for _ in range(120):
        sim.update(1.0 / sim.spec.simulation_tick_rate)
        if sim.orbs:
            break
    assert len(sim.orbs) >= 1


def test_seed_tower_landing_always_resolves_to_emit_capable_node():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("seed_tower")
    tower = first.tower
    assert tower is not None
    sim.coins = 999

    for _ in range(20):
        tower.fire_cooldown = 0.0
        sim.orbs.clear()
        sim.seed_flights.clear()
        sim._attempt_fire_tower(tower)
        assert len(sim.seed_flights) == 1
        flight = next(iter(sim.seed_flights.values()))
        assert sim._legal_segments_from_node(flight.target_node_id, None, flight.current_tier)
        for _ in range(200):
            sim._update_seed_flights(1.0 / sim.spec.simulation_tick_rate)
            if sim.orbs:
                break
        assert len(sim.orbs) == 1


def test_recall_mode_seed_landing_always_releases_an_orb():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("seed_tower")
    tower = first.tower
    assert tower is not None
    sim.coins = 999
    assert sim.purchase_secondary_mode()
    assert sim.toggle_selected_mode()

    for _ in range(20):
        tower.fire_cooldown = 0.0
        sim.orbs.clear()
        sim.seed_flights.clear()
        sim._attempt_fire_tower(tower)
        assert len(sim.seed_flights) == 1
        flight = next(iter(sim.seed_flights.values()))
        assert sim._legal_segments_from_node(flight.target_node_id, None, flight.current_tier)
        for _ in range(200):
            sim._update_seed_flights(1.0 / sim.spec.simulation_tick_rate)
            if sim.orbs:
                break
        assert len(sim.orbs) == 1


def test_power_funding_is_locked_while_active():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.power.charged = True
    assert sim.deploy_power_to_selected()
    sim.coins = 999
    assert sim.fund_power() is False


def test_same_step_red_green_spread_conflict_keeps_existing_color():
    sim = GameSimulation(default_spec())
    target_segment = None
    red_source = None
    green_source = None
    for segment_id, segment in sim.topology.segments.items():
        neighbors = [
            other_id
            for other_id in sim._neighbor_segments(segment_id)
            if sim.topology.segments[other_id].tier == segment.tier
        ]
        if len(neighbors) >= 2:
            target_segment = segment_id
            red_source = neighbors[0]
            green_source = neighbors[1]
            break
    assert target_segment is not None
    sim.segment_states[target_segment].color = "blue"
    sim.segment_states[target_segment].intensity = 0
    sim.segment_states[red_source].color = "red"
    sim.segment_states[red_source].intensity = 1
    sim.segment_states[green_source].color = "green"
    sim.segment_states[green_source].intensity = 1
    sim.random.random = lambda: 0.0
    sim._resolve_spread_step(red_due=True, green_due=True)
    assert sim.segment_states[target_segment].color == "blue"


def test_power_override_selected_snapshot_reports_power_state():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("basic_tower")
    sim.power.charged = True
    assert sim.deploy_power_to_selected()
    snapshot = sim.selected_object_snapshot()
    assert snapshot["kind"] == "power"
    assert snapshot["name"] == "Power Tower"
    assert snapshot["underlying_tower_name"] == "Basic Tower"
    availability = sim.action_availability()
    assert availability["buy_secondary"][0] is False
    assert availability["upgrade_fire_rate"][0] is False


def test_power_override_restores_suspended_tower_cooldowns_intact():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("basic_tower")
    tower = first.tower
    assert tower is not None
    tower.fire_cooldown = 0.8
    tower.swap_cooldown = 1.7
    sim.power.charged = True
    assert sim.deploy_power_to_selected()

    for _ in range(int(sim.spec.power_duration * sim.spec.simulation_tick_rate)):
        sim.update(1.0 / sim.spec.simulation_tick_rate)

    restored = first.tower
    assert restored is tower
    assert restored.fire_cooldown == 0.8
    assert restored.swap_cooldown == 1.7


def test_action_availability_and_upgrade_preview_cover_batch_2_ui_logic():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    availability = sim.action_availability()
    assert availability["build_basic_tower"][0] is True
    sim.build_tower("seed_tower")
    availability = sim.action_availability()
    assert availability["buy_secondary"][0] is True
    previews = sim.upgrade_preview()
    assert any(line.startswith("HP:") for line in previews)
    assert any(line.startswith("Snake Speed:") for line in previews)
    assert any(line.startswith("Shot Range:") for line in previews)
    assert availability["seed_closest_plus"][0] is True


def test_focus_mode_equal_angle_ties_use_randomized_tie_break():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("burst_tower")
    tower = first.tower
    assert tower is not None
    tower.secondary_unlocked = True
    tower.active_mode = "secondary"

    center_id = None
    prev_id = None
    for node_id, segs in sim.topology.adjacency.items():
        node = sim.topology.nodes[node_id]
        neighbors = [sim.topology.nodes[sim._far_endpoint(node_id, segment_id)] for segment_id in segs]
        has_left = any(neighbor.x < node.x for neighbor in neighbors)
        has_right = any(neighbor.x > node.x for neighbor in neighbors)
        has_up = any(neighbor.y < node.y for neighbor in neighbors)
        has_down = any(neighbor.y > node.y for neighbor in neighbors)
        if has_left and has_right and has_up and has_down:
            center_id = node_id
            prev_id = next(
                neighbor.key for neighbor in neighbors if neighbor.y > node.y and neighbor.x == node.x
            )
            break
    assert center_id is not None
    legal = sim._legal_segments_from_node(center_id, prev_id, "small")
    heading = sim._heading(prev_id, center_id)
    straight = next(
        segment_id
        for segment_id in legal
        if sim._angle_for_segment(center_id, heading, segment_id) == 0.0
    )
    side_candidates = [
        segment_id
        for segment_id in legal
        if sim._angle_for_segment(center_id, heading, segment_id) == 90.0
    ][:2]
    candidates = [straight, *side_candidates]
    orb = type("OrbStub", (), {"from_node": prev_id, "mode": "secondary", "burst_bias_forward": 0.01})()

    values = iter([0.1, 0.9, 0.2, 0.95])
    sim.random.random = lambda: next(values)
    first_choice = sim._select_segment_for_tower(tower, orb, center_id, candidates)

    values = iter([0.9, 0.1, 0.2, 0.95])
    sim.random.random = lambda: next(values)
    second_choice = sim._select_segment_for_tower(tower, orb, center_id, candidates)

    assert first_choice != second_choice


def test_orb_trail_points_extend_across_previous_segment_when_needed():
    sim = GameSimulation(default_spec())
    node_id = next(node_id for node_id, segments in sim.topology.adjacency.items() if len(segments) >= 2)
    current_segment_id, previous_segment_id = sim.topology.adjacency[node_id][:2]
    current_to_node = sim._far_endpoint(node_id, current_segment_id)
    previous_node = sim._far_endpoint(node_id, previous_segment_id)
    orb = Orb(
        key="orb_test",
        owner_tower_id="power_tower",
        owner_hardpoint_id=next(iter(sim.hardpoints)),
        segment_id=current_segment_id,
        from_node=node_id,
        to_node=current_to_node,
        distance_on_segment=3.0,
        lifetime_remaining=1.0,
        speed=10.0,
        damage=1.0,
        clean_rate=0.0,
        harvest_rate=0.0,
        turn_chance=0.0,
        current_tier="small",
        mode="power",
        home_node_id=node_id,
        previous_node=previous_node,
    )

    points = build_orb_trail_points(sim.topology, orb, trail_length=12.0)

    assert len(points) == 3
    assert points[0] != points[1]
    assert points[1] != points[2]


def test_orb_trail_points_follow_multiple_connected_segments():
    sim = GameSimulation(default_spec())
    center_id = next(node_id for node_id, segments in sim.topology.adjacency.items() if len(segments) >= 4)
    previous_node = sim._far_endpoint(center_id, sim.topology.adjacency[center_id][0])
    older_segment_id = next(
        segment_id
        for segment_id in sim.topology.adjacency[previous_node]
        if sim._far_endpoint(previous_node, segment_id) != center_id
    )
    older_node = sim._far_endpoint(previous_node, older_segment_id)
    oldest_segment_id = next(
        segment_id
        for segment_id in sim.topology.adjacency[older_node]
        if sim._far_endpoint(older_node, segment_id) != previous_node
    )
    oldest_node = sim._far_endpoint(older_node, oldest_segment_id)
    current_segment_id = next(
        segment_id
        for segment_id in sim.topology.adjacency[center_id]
        if sim._far_endpoint(center_id, segment_id) != previous_node
    )
    current_to_node = sim._far_endpoint(center_id, current_segment_id)
    orb = Orb(
        key="orb_turns",
        owner_tower_id="power_tower",
        owner_hardpoint_id=next(iter(sim.hardpoints)),
        segment_id=current_segment_id,
        from_node=center_id,
        to_node=current_to_node,
        distance_on_segment=5.0,
        lifetime_remaining=1.0,
        speed=10.0,
        damage=1.0,
        clean_rate=0.0,
        harvest_rate=0.0,
        turn_chance=0.0,
        current_tier="small",
        mode="power",
        home_node_id=center_id,
        previous_node=previous_node,
        trail_nodes=[previous_node, older_node, oldest_node],
    )

    points = build_orb_trail_points(sim.topology, orb, trail_length=200.0)

    assert len(points) >= 4
    assert points[1] == (sim.topology.nodes[center_id].x, sim.topology.nodes[center_id].y)
    assert points[2] == (sim.topology.nodes[previous_node].x, sim.topology.nodes[previous_node].y)


def test_faded_trail_segments_dim_toward_tail():
    segments = build_faded_trail_segments([(0.0, 0.0), (20.0, 0.0), (40.0, 0.0)], segment_length=10.0)

    assert len(segments) >= 3
    assert segments[0][2] > segments[-1][2]
    assert blend_hex("#66D9FF", "#0B1622", segments[0][2]) != blend_hex("#66D9FF", "#0B1622", segments[-1][2])


def test_orb_state_change_triggers_visible_segment_impact():
    sim = GameSimulation(default_spec())
    segment_id = next(iter(sim.segment_states))
    sim.segment_states[segment_id].color = "red"
    sim.segment_states[segment_id].intensity = 1
    sim.segment_states[segment_id].clean_progress = sim.spec.red_clean_thresholds[0] - 0.01
    orb = type("OrbStub", (), {"clean_rate": 1.0, "harvest_rate": 0.0})()

    sim._apply_orb_to_segment(segment_id, 0.02, orb)

    assert segment_id in sim.segment_impacts
    assert sim.segment_impacts[segment_id].color == "blue"
    assert sim.segment_impacts[segment_id].effect == "clean"


def test_harvest_income_creates_popup_and_selected_tower_economy_snapshot():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("basic_tower")
    tower = first.tower
    assert tower is not None

    segment_id = next(iter(sim.segment_states))
    segment = sim.topology.segments[segment_id]
    sim.segment_states[segment_id].color = "green"
    sim.segment_states[segment_id].intensity = 1
    sim.segment_states[segment_id].harvest_progress = sim.spec.green_harvest_thresholds[0] - 0.01
    orb = Orb(
        key="orb_harvest",
        owner_tower_id=tower.key,
        owner_hardpoint_id=tower.hardpoint_id,
        segment_id=segment_id,
        from_node=segment.a,
        to_node=segment.b,
        distance_on_segment=0.0,
        lifetime_remaining=1.0,
        speed=10.0,
        damage=0.0,
        clean_rate=0.0,
        harvest_rate=1.0,
        turn_chance=0.0,
        current_tier=segment.tier,
        mode="default",
        home_node_id=first.hardpoint.node_id,
    )

    sim._apply_orb_to_segment(segment_id, 0.02, orb)

    assert len(sim.harvest_popups) == 1
    hud = sim.hud_snapshot()
    assert hud["recent_harvest_event"]["amount"] == sim.spec.harvest_income_green[0]
    assert hud["recent_harvest_event"]["tower_name"] == "Basic Tower"
    assert hud["selected_tower_economy"]["recent_harvest_income"] == sim.spec.harvest_income_green[0]
    assert hud["selected_tower_economy"]["shot_cost"] == 2.0


def test_phase_promotions_are_one_way_and_hud_reports_persistent_phase_state():
    sim = GameSimulation(default_spec())

    hud = sim.hud_snapshot()
    assert hud["active_phase"] == "opening_containment"
    assert hud["active_phase_label"] == "Opening Containment"
    assert hud["highest_phase_reached"] == "opening_containment"
    assert hud["phase_transition"] is None

    sim.level = 4
    sim._evaluate_phase_state()
    hud = sim.hud_snapshot()
    assert hud["active_phase"] == "escalation"
    assert hud["highest_phase_reached"] == "escalation"
    assert hud["phase_transition"]["phase_id"] == "escalation"

    sim.level = 1
    sim.corruption_percent = lambda: 0.0
    sim._evaluate_phase_state()
    hud = sim.hud_snapshot()
    assert hud["active_phase"] == "escalation"
    assert hud["highest_phase_reached"] == "escalation"


def test_phase_can_jump_directly_to_critical_and_banner_does_not_stack():
    sim = GameSimulation(default_spec())

    sim.level = 9
    sim._evaluate_phase_state()
    hud = sim.hud_snapshot()

    assert hud["active_phase"] == "critical_load"
    assert hud["highest_phase_reached"] == "critical_load"
    assert hud["phase_transition"]["phase_id"] == "critical_load"
    assert hud["phase_transition"]["label"] == "Critical Load"
    assert sim.phase_transition_timer == 1.2


def test_corruption_seed_creates_pulse_and_enemy_telegraph_darkens():
    sim = GameSimulation(default_spec())
    node_id = next(iter(sim.topology.nodes))
    sim._seed_red_at_node(node_id, 2)
    assert len(sim.seed_pulses) == 1

    enemy = type("EnemyStub", (), {"enemy_type": "corruption_seeder", "initial_path_budget": 4, "path_budget_remaining": 4})()
    app = type("AppStub", (), {"spec": default_spec()})()
    light_color = enemy_render_color(app, enemy)
    enemy.path_budget_remaining = 1
    dark_color = enemy_render_color(app, enemy)

    assert light_color != dark_color
    assert _hex_luminance(light_color) > _hex_luminance(dark_color)


def test_sidebar_uses_contextual_action_groups():
    app = GridlineApp(default_spec())
    app.root.update()
    assert app.shell_state == "title_ready"
    assert app.utility_buttons["start_run"].winfo_manager() == "pack"
    assert app.utility_buttons["quit"].winfo_manager() == "pack"
    assert app.action_buttons["build_basic_tower"].cget("state") == "disabled"
    assert app.status_frame.cget("highlightthickness") == 1
    assert app.details_frame.cget("highlightthickness") == 1
    assert app.actions_shell.cget("highlightthickness") == 1
    assert app.utility_frame.cget("highlightthickness") == 1
    start_button = app.utility_buttons["start_run"]
    assert app.utility_frame.winfo_height() > 80
    assert start_button.winfo_height() >= 20
    assert start_button.winfo_rooty() >= app.root.winfo_rooty()

    app._start_run()
    app.root.update_idletasks()
    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert app.action_groups["build"].winfo_manager() == "pack"
    assert app.action_groups["tower"].winfo_manager() == "pack"
    assert app.action_buttons["build_basic_tower"].cget("text") == "Basic | 55c"
    assert app.action_buttons["build_basic_tower"].grid_info()["column"] == 0
    assert app.action_buttons["build_seed_tower"].grid_info()["column"] == 1
    assert app.action_buttons["build_burst_tower"].grid_info()["column"] == 2
    assert "Build priorities:" in app.detail_text.get()
    assert "reliable generalist" in app.detail_text.get()
    assert app.status_row_vars["pressure"].get().startswith("Pressure:")
    assert "Esc pauses" in app.utility_hint_text.get()
    assert app.status_row_labels["pressure"].cget("bg") != app.utility_frame.cget("bg")

    app.sim.build_tower("seed_tower")
    app._refresh_sidebar()
    app.root.update_idletasks()
    assert app.action_groups["tower"].winfo_manager() == "pack"
    assert app.action_groups["seed"].winfo_manager() == "pack"
    assert app.action_buttons["upgrade_fire_rate"].grid_info()["column"] == 0
    assert app.action_buttons["upgrade_hp"].grid_info()["column"] == 1

    app._quit_app()


def test_empty_hardpoint_selection_resets_action_scroll_to_build_controls():
    app = GridlineApp(default_spec())
    app.root.update()
    hardpoints = list(app.sim.hardpoints.values())
    occupied = hardpoints[0]
    empty = hardpoints[1]
    app.sim.selected_hardpoint_id = occupied.hardpoint.key
    app.sim.build_tower("seed_tower")
    app._refresh_sidebar()
    app.root.update_idletasks()

    calls = []
    app.action_canvas.yview_moveto = lambda value: calls.append(value)
    app.sim.selected_hardpoint_id = empty.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert 0.0 in calls
    assert app.action_groups["build"].winfo_manager() == "pack"
    app._quit_app()


def test_occupied_hardpoint_selection_resets_action_scroll_to_tower_controls():
    app = GridlineApp(default_spec())
    app.root.geometry("1280x720")
    app.root.update()
    hardpoints = list(app.sim.hardpoints.values())
    first = hardpoints[0]
    second = hardpoints[1]
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app.sim.build_tower("seed_tower")
    app.sim.selected_hardpoint_id = second.hardpoint.key
    app.sim.build_tower("basic_tower")
    app._refresh_sidebar()
    app.root.update_idletasks()

    calls = []
    app.action_canvas.yview_moveto = lambda value: calls.append(value)
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert 0.0 in calls
    assert app.action_groups["tower"].winfo_y() + app.action_buttons["buy_secondary"].winfo_height() <= app.action_canvas.winfo_height()
    app._quit_app()


def test_action_group_positions_stay_stationary_through_selection_changes():
    app = GridlineApp(default_spec())
    app.root.update()
    hardpoints = list(app.sim.hardpoints.values())
    empty = hardpoints[1]
    occupied = hardpoints[0]

    app.sim.selected_hardpoint_id = empty.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()
    empty_positions = {
        key: app.action_groups[key].winfo_y()
        for key in ("tower", "seed", "power")
    }

    app.sim.selected_hardpoint_id = occupied.hardpoint.key
    app.sim.build_tower("seed_tower")
    app._refresh_sidebar()
    app.root.update_idletasks()
    occupied_positions = {
        key: app.action_groups[key].winfo_y()
        for key in ("tower", "seed", "power")
    }

    assert occupied_positions == empty_positions
    app._quit_app()


def test_sidebar_uses_explicit_secondary_mode_names_in_details_and_actions():
    app = GridlineApp(default_spec())
    app.root.update()
    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app.sim.build_tower("seed_tower")
    tower = first.tower
    assert tower is not None
    app.sim.coins = 999
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert app.action_buttons["buy_secondary"].cget("text") == "Buy Recall"
    assert "Mode: Default" in app.detail_text.get()

    assert app.sim.purchase_secondary_mode()
    assert app.sim.toggle_selected_mode()
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "Mode: Recall Mode" in app.detail_text.get()
    assert "Recall Mode unlocked: Yes" in app.detail_text.get()
    assert app.action_buttons["swap_mode"].cget("text").startswith("To Default | Cooldown")

    app._quit_app()


def test_power_status_and_actions_show_funding_and_ready_state_clearly():
    app = GridlineApp(default_spec())
    app.root.update()
    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "Phase: [OPENING] Opening Containment" in app.status_text.get()
    assert "Power: [FUNDING] [.........." in app.status_text.get()
    assert app.action_buttons["fund_power"].cget("text") == "Fund +10% | 45c"

    app.sim.power.charged = True
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "Power: [READY] [##########] 100%" in app.status_text.get()
    assert app.action_buttons["deploy_power"].cget("text") == "Deploy | Ready"

    app._quit_app()


def test_disabled_actions_show_reason_in_place_and_success_feedback_updates():
    app = GridlineApp(default_spec())
    app.root.update()
    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app.sim.coins = 0
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "Need 55c" in app.action_buttons["build_basic_tower"].cget("text")

    app.sim.coins = 999
    app._run_action("fund_power", lambda: app.sim.fund_power())
    app.root.update_idletasks()

    assert app.feedback_text.get() == "Power funding: 0% -> 10%."
    app._quit_app()


def test_selection_region_handles_long_detail_overflow_inside_its_own_scroll_body():
    app = GridlineApp(default_spec())
    app.root.geometry("1280x720")
    app.root.update()
    app.detail_text.set("\n".join(f"Detail line {index}" for index in range(18)))
    app.feedback_text.set("\n".join(f"Feedback line {index}" for index in range(6)))
    app.upgrade_text.set("\n".join(f"Upgrade line {index}" for index in range(8)))
    app._queue_sidebar_rebalance()
    app.root.update_idletasks()

    assert app.detail_canvas.winfo_height() > 0
    assert app.detail_inner.winfo_reqheight() > app.detail_canvas.winfo_height()
    assert app.action_canvas.winfo_height() >= 156
    app._quit_app()


def test_harvest_impact_uses_distinct_effect_type():
    sim = GameSimulation(default_spec())
    first = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first.hardpoint.key
    sim.build_tower("basic_tower")
    tower = first.tower
    assert tower is not None

    segment_id = next(iter(sim.segment_states))
    segment = sim.topology.segments[segment_id]
    sim.segment_states[segment_id].color = "green"
    sim.segment_states[segment_id].intensity = 1
    sim.segment_states[segment_id].harvest_progress = sim.spec.green_harvest_thresholds[0] - 0.01
    orb = Orb(
        key="orb_harvest_effect",
        owner_tower_id=tower.key,
        owner_hardpoint_id=tower.hardpoint_id,
        segment_id=segment_id,
        from_node=segment.a,
        to_node=segment.b,
        distance_on_segment=0.0,
        lifetime_remaining=1.0,
        speed=10.0,
        damage=0.0,
        clean_rate=0.0,
        harvest_rate=1.0,
        turn_chance=0.0,
        current_tier=segment.tier,
        mode="default",
        home_node_id=first.hardpoint.node_id,
    )

    sim._apply_orb_to_segment(segment_id, 0.02, orb)

    assert sim.segment_impacts[segment_id].effect == "harvest"


def test_basic_tower_default_prefers_interior_at_first_eligible_turn_from_top_edge():
    sim = GameSimulation(default_spec())
    top_node_id = next(
        node_id
        for node_id, node in sim.topology.nodes.items()
        if "large" in node.tiers and node.y == sim.topology.playfield_rect[1] and len(sim.topology.adjacency[node_id]) >= 3
    )
    inward_turn_node_id = next(
        sim._far_endpoint(top_node_id, segment_id)
        for segment_id in sim.topology.adjacency[top_node_id]
        if sim.topology.nodes[sim._far_endpoint(top_node_id, segment_id)].y == sim.topology.playfield_rect[1]
    )
    prev_node_id = next(
        sim._far_endpoint(top_node_id, segment_id)
        for segment_id in sim.topology.adjacency[top_node_id]
        if sim._far_endpoint(top_node_id, segment_id) != inward_turn_node_id
        and sim.topology.nodes[sim._far_endpoint(top_node_id, segment_id)].y == sim.topology.playfield_rect[1]
    )
    first_hardpoint = next(iter(sim.hardpoints.values()))
    sim.selected_hardpoint_id = first_hardpoint.hardpoint.key
    sim.build_tower("basic_tower")
    tower = first_hardpoint.tower
    assert tower is not None
    orb = type(
        "OrbStub",
        (),
        {
            "from_node": prev_node_id,
            "mode": "default",
            "interior_bias_edge": "top",
            "interior_bias_remaining": float(sim.spec.large_spacing),
        },
    )()

    candidates = sim._legal_segments_from_node(top_node_id, prev_node_id, "large")
    chosen = sim._select_segment_for_tower(tower, orb, top_node_id, candidates)
    target = sim.topology.nodes[sim._far_endpoint(top_node_id, chosen)]
    assert target.y > sim.topology.playfield_rect[1]


def test_seed_tower_default_targets_prefer_interior_nodes_when_available():
    sim = GameSimulation(default_spec())
    hardpoint = next(item for item in sim.hardpoints.values() if item.hardpoint.side == "top")
    sim.selected_hardpoint_id = hardpoint.hardpoint.key
    sim.build_tower("seed_tower")
    tower = hardpoint.tower
    assert tower is not None

    for _ in range(10):
        target_node_id = sim._select_seed_target(tower, hardpoint.hardpoint.node_id, sim.shot_range_value(tower))
        assert target_node_id is not None
        assert sim._is_node_interior_preferred(target_node_id, "top")


def test_topology_respects_playfield_viewport_override_for_hardpoint_bounds():
    spec = replace(default_spec(), playfield_width=936, playfield_height=640)
    topology = build_topology(spec)
    _, _, _, bottom = topology.playfield_rect
    max_hardpoint_y = max(topology.nodes[hardpoint.node_id].y for hardpoint in topology.hardpoints)

    assert len(topology.hardpoints) == 12
    assert bottom <= 616
    assert max_hardpoint_y <= bottom


def test_rendered_board_surface_uses_topology_playfield_rect():
    app = GridlineApp(default_spec())
    app.root.update()
    app._render()
    app.root.update_idletasks()

    board_items = app.canvas.find_withtag("board_surface")
    assert len(board_items) == 1
    coords = tuple(round(value, 2) for value in app.canvas.coords(board_items[0]))
    expected = tuple(round(value, 2) for value in app.sim.topology.playfield_rect)
    assert coords == expected
    app._quit_app()


def test_shell_flow_boot_pause_resume_and_defeat_replay():
    app = GridlineApp(default_spec())
    app.root.update()

    assert app.shell_state == "title_ready"
    assert app.loop_running is False
    ready_text = "\n".join(
        app.canvas.itemcget(item, "text")
        for item in app.canvas.find_withtag("shell_overlay")
        if app.canvas.type(item) == "text"
    )
    assert "READY SHELL" in ready_text
    assert "GRIDLINE READY" in ready_text
    assert "PRIMARY // Start Run" in ready_text
    assert app.utility_buttons["start_run"].cget("bg") == "#245985"
    assert app.utility_buttons["quit"].cget("bg") == "#132235"

    app._start_run()
    app.root.update_idletasks()
    assert app.shell_state == "active_run"
    assert app.utility_buttons["start_run"].winfo_manager() == ""

    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    selected_before_pause = app.sim.selected_hardpoint_id
    app.sim.run_time = 12.5
    app._on_escape()

    assert app.shell_state == "paused"
    assert app.sim.selected_hardpoint_id == selected_before_pause
    paused_time = app.sim.run_time
    app._loop()
    assert app.sim.run_time == paused_time
    assert app.utility_buttons["resume"].winfo_manager() == "pack"
    assert app.utility_buttons["replay"].winfo_manager() == "pack"
    assert app.utility_buttons["quit"].winfo_manager() == "pack"
    paused_text = "\n".join(
        app.canvas.itemcget(item, "text")
        for item in app.canvas.find_withtag("shell_overlay")
        if app.canvas.type(item) == "text"
    )
    assert "PAUSE SHELL" in paused_text
    assert "RUN PAUSED" in paused_text
    assert "PRIMARY // Resume" in paused_text
    assert app.utility_buttons["resume"].cget("bg") == "#245985"
    assert app.utility_buttons["replay"].cget("bg") == "#132235"

    app._on_escape()
    assert app.shell_state == "active_run"

    app.sim.level = 9
    app.sim._evaluate_phase_state()
    app._refresh_sidebar()
    app._render()
    app.root.update_idletasks()
    phase_banner_text = "\n".join(
        app.canvas.itemcget(item, "text")
        for item in app.canvas.find_withtag("phase_banner")
        if app.canvas.type(item) == "text"
    )
    assert "CRITICAL // Critical Load" in phase_banner_text
    assert "Late-crisis recovery and power timing are live." in phase_banner_text
    assert "Phase: [SHIFT] [CRITICAL] Critical Load" in app.status_text.get()

    app.sim.run_time = 98.0
    app.highest_power_funding = 80
    app.power_deploy_count = 2
    app.sim.game_over = True
    app._transition_to_defeat()

    assert app.shell_state == "defeat_summary"
    assert "Cause of loss: Corruption threshold exceeded" in app.detail_text.get()
    assert "Run duration: 98.0s" in app.detail_text.get()
    assert app.utility_buttons["replay"].winfo_manager() == "pack"
    assert app.utility_buttons["quit"].winfo_manager() == "pack"
    assert app.utility_buttons["resume"].winfo_manager() == ""
    defeat_text = "\n".join(
        app.canvas.itemcget(item, "text")
        for item in app.canvas.find_withtag("shell_overlay")
        if app.canvas.type(item) == "text"
    )
    assert "DEFEAT SHELL" in defeat_text
    assert "GRID FAILURE" in defeat_text
    assert "PRIMARY // Replay" in defeat_text
    assert "Cause of loss: Corruption threshold exceeded" in defeat_text
    assert "Run duration: 98.0s" in defeat_text
    assert "Highest phase reached: Critical Load" in defeat_text
    assert "Corruption at loss:" in defeat_text
    assert "Power usage: 80% peak funding, 2 deploys" in defeat_text
    assert defeat_text.index("Cause of loss: Corruption threshold exceeded") < defeat_text.index("Run duration: 98.0s")
    assert defeat_text.index("Run duration: 98.0s") < defeat_text.index("Highest phase reached: Critical Load")
    assert defeat_text.index("Highest phase reached: Critical Load") < defeat_text.index("Corruption at loss:")
    assert defeat_text.index("Corruption at loss:") < defeat_text.index("Power usage: 80% peak funding, 2 deploys")
    assert app.utility_buttons["replay"].cget("bg") == "#245985"
    assert app.utility_buttons["quit"].cget("bg") == "#132235"

    app._replay_run()
    assert app.shell_state == "active_run"
    assert app.sim.run_time == 0.0
    assert app.power_deploy_count == 0
    assert app.highest_power_funding == 0

    app._quit_app()


def test_live_config_opener_styles_reach_the_minute_two_checkpoint_window():
    spec = load_game_spec("game_config.json")

    def run(style: str) -> float:
        sim = GameSimulation(spec)
        hardpoints = list(sim.hardpoints.values())
        if style == "basic_only":
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            sim.build_tower("basic_tower")
        elif style == "mixed_three":
            for hardpoint, tower_key in zip(hardpoints[:3], ("basic_tower", "seed_tower", "burst_tower")):
                sim.selected_hardpoint_id = hardpoint.hardpoint.key
                sim.build_tower(tower_key)
        elif style == "upgrade_first":
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            sim.build_tower("basic_tower")
            sim.upgrade_selected_tower_type("fire_rate")
        else:
            raise AssertionError(style)

        elapsed = 0.0
        dt = 1.0 / sim.spec.simulation_tick_rate
        while not sim.game_over and elapsed < 180.0:
            sim.update(dt)
            elapsed += dt
        return elapsed

    for style in ("basic_only", "mixed_three", "upgrade_first"):
        assert run(style) >= 120.0, style


def test_live_config_power_rush_can_reach_a_real_power_deploy_window():
    spec = load_game_spec("game_config.json")
    sim = GameSimulation(spec)
    hardpoints = list(sim.hardpoints.values())
    sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
    assert sim.build_tower("basic_tower")

    elapsed = 0.0
    dt = 1.0 / sim.spec.simulation_tick_rate
    charged = False
    deployed = False
    highest_funding = 0

    while not sim.game_over and elapsed < 180.0:
        built_count = len([item for item in hardpoints[:3] if item.tower is not None])
        # Keep this line power-leaning, but do not let it starve the board so hard
        # that the new late-use timing gate becomes impossible by construction.
        if built_count < 2 and (elapsed >= 35.0 or sim.power.funding_percent >= 30):
            sim.selected_hardpoint_id = hardpoints[1].hardpoint.key
            sim.build_tower("seed_tower")
        elif built_count < 3 and (elapsed >= 70.0 or sim.power.funding_percent >= 60):
            sim.selected_hardpoint_id = hardpoints[2].hardpoint.key
            sim.build_tower("basic_tower")
        elif sim.fund_power_preview()[0]:
            sim.fund_power()
        highest_funding = max(highest_funding, sim.power.funding_percent)
        if sim.power.charged:
            charged = True
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            if sim.action_availability()["deploy_power"][0]:
                deployed = sim.deploy_power_to_selected() or deployed
        sim.update(dt)
        elapsed += dt

    assert charged or deployed or highest_funding >= 60


def test_live_config_starting_economy_cannot_buy_full_power_charge_immediately():
    spec = load_game_spec("game_config.json")
    assert spec.starting_coins < spec.power_funding_chunk_cost * 10

    sim = GameSimulation(spec)
    while sim.fund_power_preview()[0]:
        sim.fund_power()

    assert sim.power.funding_percent < 100
    assert sim.power.charged is False


def _run_live_config_mixed_late_funding_follow_up(seed: int) -> dict[str, int | bool]:
    spec = load_game_spec("game_config.json")
    sim = GameSimulation(spec, seed=seed)
    hardpoints = list(sim.hardpoints.values())
    elapsed = 0.0
    dt = 1.0 / sim.spec.simulation_tick_rate
    highest_funding = 0
    charged = False
    deploy_count = 0

    while not sim.game_over and elapsed < 360.0:
        if hardpoints[0].tower is None:
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            sim.build_tower("basic_tower")
        elif hardpoints[1].tower is None and elapsed >= 20.0:
            sim.selected_hardpoint_id = hardpoints[1].hardpoint.key
            sim.build_tower("seed_tower")
        elif hardpoints[2].tower is None and elapsed >= 55.0:
            sim.selected_hardpoint_id = hardpoints[2].hardpoint.key
            sim.build_tower("burst_tower")
        elif elapsed >= 90.0 and sim.fund_power_preview()[0]:
            sim.fund_power()
        highest_funding = max(highest_funding, sim.power.funding_percent)
        if sim.power.charged:
            charged = True
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            if sim.action_availability()["deploy_power"][0]:
                if sim.deploy_power_to_selected():
                    deploy_count += 1
        sim.update(dt)
        elapsed += dt

    return {
        "highest_funding": highest_funding,
        "charged": charged,
        "deploy_count": deploy_count,
    }


def _run_live_config_delayed_power_follow_up(seed: int) -> dict[str, int | bool]:
    spec = load_game_spec("game_config.json")
    sim = GameSimulation(spec, seed=seed)
    hardpoints = list(sim.hardpoints.values())
    elapsed = 0.0
    dt = 1.0 / sim.spec.simulation_tick_rate
    highest_funding = 0
    charged = False
    deploy_count = 0

    while not sim.game_over and elapsed < 360.0:
        if hardpoints[0].tower is None:
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            sim.build_tower("basic_tower")
        elif elapsed < 18.0:
            pass
        elif sim.power.funding_percent < 30 and sim.fund_power_preview()[0]:
            sim.fund_power()
        elif hardpoints[1].tower is None and elapsed >= 40.0:
            sim.selected_hardpoint_id = hardpoints[1].hardpoint.key
            sim.build_tower("seed_tower")
        elif elapsed >= 70.0 and sim.power.funding_percent < 60 and sim.fund_power_preview()[0]:
            sim.fund_power()
        elif hardpoints[2].tower is None and elapsed >= 95.0:
            sim.selected_hardpoint_id = hardpoints[2].hardpoint.key
            sim.build_tower("basic_tower")
        elif elapsed >= 120.0 and sim.fund_power_preview()[0]:
            sim.fund_power()
        highest_funding = max(highest_funding, sim.power.funding_percent)
        if sim.power.charged:
            charged = True
            sim.selected_hardpoint_id = hardpoints[0].hardpoint.key
            if sim.action_availability()["deploy_power"][0]:
                if sim.deploy_power_to_selected():
                    deploy_count += 1
        sim.update(dt)
        elapsed += dt

    return {
        "highest_funding": highest_funding,
        "charged": charged,
        "deploy_count": deploy_count,
    }


def test_live_config_mixed_follow_up_reaches_a_broader_late_funding_window():
    results = [
        _run_live_config_mixed_late_funding_follow_up(seed)
        for seed in (1, 7, 13)
    ]
    highest_by_seed = [int(result["highest_funding"]) for result in results]

    assert min(highest_by_seed) >= 60
    assert max(highest_by_seed) >= 100
    assert any(bool(result["charged"]) or int(result["deploy_count"]) > 0 for result in results)


def test_live_config_delayed_power_follow_up_holds_the_late_funding_floor():
    results = [
        _run_live_config_delayed_power_follow_up(seed)
        for seed in (1, 7, 13)
    ]
    highest_by_seed = [int(result["highest_funding"]) for result in results]

    assert min(highest_by_seed) >= 60
    assert all(bool(result["charged"]) or int(result["deploy_count"]) > 0 for result in results)


def _hex_luminance(color: str) -> int:
    return sum(int(color[index:index + 2], 16) for index in (1, 3, 5))
