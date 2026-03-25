from __future__ import annotations

from dataclasses import dataclass, field
import math

from .spec import TIER_INDEX, TIER_ORDER, GameSpec


@dataclass
class Node:
    key: str
    x: float
    y: float
    tiers: set[str] = field(default_factory=set)
    segment_ids: set[str] = field(default_factory=set)


@dataclass
class Segment:
    key: str
    a: str
    b: str
    tier: str
    length: float


@dataclass
class Hardpoint:
    key: str
    node_id: str
    side: str


@dataclass
class Topology:
    nodes: dict[str, Node]
    segments: dict[str, Segment]
    adjacency: dict[str, list[str]]
    hardpoints: list[Hardpoint]
    playfield_rect: tuple[float, float, float, float]
    center: tuple[float, float]

    def segment_midpoint(self, segment_id: str) -> tuple[float, float]:
        segment = self.segments[segment_id]
        a = self.nodes[segment.a]
        b = self.nodes[segment.b]
        return ((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)


def build_topology(spec: GameSpec) -> Topology:
    left = spec.playfield_margin_left
    top = spec.playfield_margin_top
    right_inset = _playfield_right_inset(spec)
    playfield_width = spec.playfield_width if spec.playfield_width is not None else spec.width
    playfield_height = spec.playfield_height if spec.playfield_height is not None else spec.height
    right = playfield_width - right_inset
    bottom = playfield_height - spec.playfield_margin_bottom
    width = right - left
    height = bottom - top
    large_right = left
    large_bottom = top

    nodes: dict[str, Node] = {}
    segments: dict[str, Segment] = {}
    adjacency: dict[str, list[str]] = {}

    def get_node(x: float, y: float, tier: str) -> str:
        key = f"{round(x, 2)}:{round(y, 2)}"
        node = nodes.get(key)
        if node is None:
            node = Node(key=key, x=x, y=y)
            nodes[key] = node
        node.tiers.add(tier)
        adjacency.setdefault(key, [])
        return key

    def add_segment(a_id: str, b_id: str, tier: str) -> None:
        pair = tuple(sorted((a_id, b_id)))
        key = f"{tier}:{pair[0]}->{pair[1]}"
        if key in segments:
            return
        a = nodes[a_id]
        b = nodes[b_id]
        segment = Segment(key=key, a=a_id, b=b_id, tier=tier, length=math.dist((a.x, a.y), (b.x, b.y)))
        segments[key] = segment
        nodes[a_id].segment_ids.add(key)
        nodes[b_id].segment_ids.add(key)
        adjacency[a_id].append(key)
        adjacency[b_id].append(key)

    for tier, spacing in (
        ("large", spec.large_spacing),
        ("medium", spec.medium_spacing),
        ("small", spec.small_spacing),
    ):
        cols = int(width // spacing)
        rows = int(height // spacing)
        if tier == "large":
            large_right = left + cols * spacing
            large_bottom = top + rows * spacing
        for col in range(cols + 1):
            x = left + col * spacing
            for row in range(rows + 1):
                y = top + row * spacing
                get_node(x, y, tier)
        for col in range(cols + 1):
            x = left + col * spacing
            for row in range(rows):
                add_segment(get_node(x, top + row * spacing, tier), get_node(x, top + (row + 1) * spacing, tier), tier)
        for row in range(rows + 1):
            y = top + row * spacing
            for col in range(cols):
                add_segment(get_node(left + col * spacing, y, tier), get_node(left + (col + 1) * spacing, y, tier), tier)

    perimeter_large_nodes = [node for node in nodes.values() if "large" in node.tiers and _is_perimeter(node, left, top, large_right, large_bottom)]
    hardpoint_nodes = _select_hardpoint_nodes(perimeter_large_nodes, left, top, large_right, large_bottom, spec.hardpoint_count)
    hardpoints = [
        Hardpoint(
            key=f"hardpoint_{index}",
            node_id=node.key,
            side=_node_side(node, left, top, large_right, large_bottom),
        )
        for index, node in enumerate(hardpoint_nodes)
    ]
    return Topology(
        nodes=nodes,
        segments=segments,
        adjacency=adjacency,
        hardpoints=hardpoints,
        playfield_rect=(left, top, large_right, large_bottom),
        center=(left + (large_right - left) / 2, top + (large_bottom - top) / 2),
    )


def _is_perimeter(node: Node, left: float, top: float, right: float, bottom: float) -> bool:
    return (
        math.isclose(node.x, left)
        or math.isclose(node.x, right)
        or math.isclose(node.y, top)
        or math.isclose(node.y, bottom)
    )


def _node_side(node: Node, left: float, top: float, right: float, bottom: float) -> str:
    if math.isclose(node.y, top):
        return "top"
    if math.isclose(node.y, bottom):
        return "bottom"
    if math.isclose(node.x, left):
        return "left"
    return "right"


def _select_hardpoint_nodes(nodes: list[Node], left: float, top: float, right: float, bottom: float, count: int) -> list[Node]:
    by_side = {"top": [], "bottom": [], "left": [], "right": []}
    for node in nodes:
        by_side[_node_side(node, left, top, right, bottom)].append(node)
    by_side["top"].sort(key=lambda node: node.x)
    by_side["bottom"].sort(key=lambda node: node.x)
    by_side["left"].sort(key=lambda node: node.y)
    by_side["right"].sort(key=lambda node: node.y)
    desired = max(1, count // 4)
    picked: list[Node] = []
    for side in ("top", "bottom", "left", "right"):
        side_nodes = [
            node
            for node in by_side[side]
            if not (
                (math.isclose(node.x, left) or math.isclose(node.x, right))
                and (math.isclose(node.y, top) or math.isclose(node.y, bottom))
            )
        ]
        if not side_nodes:
            side_nodes = by_side[side]
        if not side_nodes:
            continue
        last_index = len(side_nodes) - 1
        for slot in range(min(desired, len(side_nodes))):
            index = round(slot * last_index / max(1, desired - 1))
            picked.append(side_nodes[index])
    return picked[:count]


def allowed_tiers(max_tier: str) -> set[str]:
    max_index = TIER_INDEX[max_tier]
    return {tier for tier, index in TIER_INDEX.items() if index <= max_index}


def _playfield_right_inset(spec: GameSpec) -> int:
    if spec.playfield_width is not None:
        return max(spec.playfield_margin_left, spec.playfield_margin_right - spec.visuals.sidebar_width)
    return spec.playfield_margin_right
