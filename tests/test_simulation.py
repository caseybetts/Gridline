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
    assert spec.starting_coins == 220
    assert spec.hardpoint_count == 12
    assert spec.level_interval == 45
    assert spec.harvest_income_green == (4, 8, 14)
    assert spec.towers["basic_tower"].build_cost == 55
    assert spec.towers["seed_tower"].shot_range == 340
    assert spec.enemies["tower_striker"].hp == 25
    assert spec.enemies["corruption_seeder"].hp == 18
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
    first = next(iter(app.sim.hardpoints.values()))
    app.sim.selected_hardpoint_id = first.hardpoint.key
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "new_game" in app.utility_buttons
    assert app.action_groups["build"].winfo_manager() == "pack"
    assert app.action_groups["tower"].winfo_manager() == ""

    app.sim.build_tower("seed_tower")
    app._refresh_sidebar()
    app.root.update_idletasks()
    assert app.action_groups["tower"].winfo_manager() == "pack"
    assert app.action_groups["seed"].winfo_manager() == "pack"

    app.root.destroy()


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

    assert app.action_buttons["buy_secondary"].cget("text") == "Buy Recall Mode"
    assert "Mode: Default" in app.detail_text.get()

    assert app.sim.purchase_secondary_mode()
    assert app.sim.toggle_selected_mode()
    app._refresh_sidebar()
    app.root.update_idletasks()

    assert "Mode: Recall Mode" in app.detail_text.get()
    assert "Recall Mode unlocked: Yes" in app.detail_text.get()
    assert app.action_buttons["swap_mode"].cget("text") == "Switch to Default Mode"

    app.root.destroy()


def test_topology_respects_playfield_viewport_override_for_hardpoint_bounds():
    spec = replace(default_spec(), playfield_width=936, playfield_height=640)
    topology = build_topology(spec)
    _, _, _, bottom = topology.playfield_rect
    max_hardpoint_y = max(topology.nodes[hardpoint.node_id].y for hardpoint in topology.hardpoints)

    assert len(topology.hardpoints) == 12
    assert bottom <= 616
    assert max_hardpoint_y <= bottom


def _hex_luminance(color: str) -> int:
    return sum(int(color[index:index + 2], 16) for index in (1, 3, 5))
