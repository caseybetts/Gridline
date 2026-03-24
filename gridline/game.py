from __future__ import annotations

import pygame

from gridline.config import GameConfig, load_game_config
from gridline.sim_line import GameState, LineState


DEFAULT_VISUALS = {
    "palette": {
        "background": [4, 7, 13],
        "panel": [10, 14, 22],
        "text": [204, 214, 228],
        "grid_blue": [48, 78, 126],
        "grid_green": [88, 190, 148],
        "grid_red": [186, 82, 96],
        "tower_active": [164, 176, 196],
        "tower_idle": [74, 84, 104],
        "enemy": [138, 104, 114],
        "orb_head": [240, 238, 225],
        "orb_trail": [178, 212, 232],
    },
    "grid_layer_width_by_tier": {"large": 3, "medium": 2, "small": 1},
    "grid_layer_glow_alpha_by_tier": {"large": 92, "medium": 38, "small": 14},
    "orb_trail_width": 3,
    "orb_head_radius": 5,
    "enemy_radius": 5,
    "tower_radius": 9,
    "grid_scale_multiplier": 0.5,
}


class GridlineApp:
    def __init__(self, config: GameConfig):
        pygame.init()
        pygame.display.set_caption("Gridline")
        self.config = config
        self.windowed_size = (
            config.display["window_width"],
            config.display["window_height"],
        )
        self.visuals = self._merge_visuals(config.raw.get("visuals", {}))
        self.fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.small_font = pygame.font.SysFont("consolas", 14)
        self.state = GameState(config)
        self.sidebar_width = 300
        self.cell_size = 28.0
        self.margin = 36.0
        self.grid_origin = (36.0, 36.0)
        self.playfield_rect = pygame.Rect(0, 0, 0, 0)
        self.button_rects: dict[str, pygame.Rect] = {}
        self.glow_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self.state.update(dt)
            self._draw()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit
                if event.key == pygame.K_F11 and self.config.display["fullscreen_toggle_enabled"]:
                    self._toggle_fullscreen()
                if event.key == pygame.K_1:
                    self.state.selected_tower_type_id = self.config.towers[0]["id"]
                if event.key == pygame.K_2 and len(self.config.towers) > 1:
                    self.state.selected_tower_type_id = self.config.towers[1]["id"]
                if event.key == pygame.K_3 and len(self.config.towers) > 2:
                    self.state.selected_tower_type_id = self.config.towers[2]["id"]
                if event.key == pygame.K_p:
                    self.state.deploy_power_tower()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        for hardpoint in self.state.hardpoints:
            hx, hy = self._grid_to_screen(hardpoint.x, hardpoint.y)
            radius = self.visuals["tower_radius"] + 8
            rect = pygame.Rect(hx - radius, hy - radius, radius * 2, radius * 2)
            if rect.collidepoint(pos):
                self.state.build_tower(hardpoint.index)
                return
        for action, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                if action.startswith("tower:"):
                    self.state.selected_tower_type_id = action.split(":", 1)[1]
                elif action.startswith("upgrade:"):
                    self.state.selected_upgrade = action.split(":", 1)[1]
                    self.state.upgrade_selected_tower_type()
                elif action == "fund_power":
                    self.state.fund_power_tower()
                elif action == "deploy_power":
                    self.state.deploy_power_tower()
                return

    def _draw(self) -> None:
        self._update_layout()
        self.screen.fill(self._color("background"))
        self.glow_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.button_rects.clear()
        self._draw_backdrop()
        self._draw_grid()
        self._draw_entities()
        self.screen.blit(self.glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        self._draw_hud()
        pygame.display.flip()

    def _draw_backdrop(self) -> None:
        width, height = self.screen.get_size()
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 34), pygame.Rect(0, 0, width, height))
        for band in range(0, height, 6):
            alpha = 8 if band % 12 == 0 else 3
            pygame.draw.line(vignette, (18, 14, 10, alpha), (0, band), (width, band), 1)
        for offset in range(8):
            inset = offset * 18
            alpha = max(0, 18 - offset * 2)
            pygame.draw.rect(vignette, (0, 0, 0, alpha), pygame.Rect(inset, inset, width - inset * 2, height - inset * 2), width=20)
        self.screen.blit(vignette, (0, 0))
        pygame.draw.rect(self.screen, (22, 18, 14), self.playfield_rect, width=1)

    def _draw_grid(self) -> None:
        for tier in ("small", "medium", "large"):
            width = self.visuals["grid_layer_width_by_tier"][tier]
            alpha = self.visuals["grid_layer_glow_alpha_by_tier"][tier]
            for segment in self.state.all_segments():
                if not self.state.segment_allowed_for_tier(segment.key, tier):
                    continue
                start, end = self.state.segment_endpoints(segment.key)
                a = self._grid_to_screen(start[0], start[1])
                b = self._grid_to_screen(end[0], end[1])
                glow_rgb = self._grid_base_color(tier)
                glow_extra = 3 if tier == "large" else 1 if tier == "medium" else 0
                pygame.draw.line(self.glow_surface, (*glow_rgb, alpha), a, b, width + glow_extra)
                line_rgb = tuple(max(6, int(channel * (0.20 if tier == "small" else 0.42 if tier == "medium" else 0.72))) for channel in glow_rgb)
                pygame.draw.line(self.screen, line_rgb, a, b, width)
        self._draw_grid_nodes()

        for segment in self.state.active_segments():
            start, end = self.state.segment_endpoints(segment.key)
            a = self._grid_to_screen(start[0], start[1])
            b = self._grid_to_screen(end[0], end[1])
            color_name = "grid_green" if segment.state == LineState.GREEN else "grid_red"
            glow = tuple(min(255, c + 18 * max(0, segment.intensity - 1)) for c in self._color(color_name))
            width = 3 if self.state.segment_allowed_for_tier(segment.key, "large") else 2 if self.state.segment_allowed_for_tier(segment.key, "medium") else 1
            pygame.draw.line(self.glow_surface, (*glow, 90 if segment.state == LineState.GREEN else 110), a, b, width + 3)
            pygame.draw.line(self.screen, glow, a, b, width + 1)

    def _draw_grid_nodes(self) -> None:
        for y in range(self.state.grid_height):
            for x in range(self.state.grid_width):
                sx, sy = self._grid_to_screen(x, y)
                if x % 4 == 0 and y % 4 == 0:
                    pygame.draw.circle(self.screen, (88, 78, 62), (sx, sy), 1)
                elif x % 2 == 0 and y % 2 == 0:
                    pygame.draw.circle(self.screen, (44, 38, 32), (sx, sy), 1)

    def _draw_entities(self) -> None:
        for hardpoint in self.state.hardpoints:
            sx, sy = self._grid_to_screen(hardpoint.x, hardpoint.y)
            radius = self.visuals["tower_radius"]
            color = self._color("tower_active") if hardpoint.tower else self._color("tower_idle")
            pygame.draw.circle(self.glow_surface, (*color, 26), (sx, sy), radius + 4)
            pygame.draw.circle(self.screen, color, (sx, sy), radius, width=1)
            pygame.draw.line(self.screen, color, (sx - radius - 5, sy), (sx + radius + 5, sy), 1)
            pygame.draw.line(self.screen, color, (sx, sy - radius - 5), (sx, sy + radius + 5), 1)
            if hardpoint.tower:
                hp_ratio = max(0.0, hardpoint.tower.hp / hardpoint.tower.type_state.stat("hp"))
                pygame.draw.rect(self.screen, (28, 36, 46), pygame.Rect(sx - 14, sy - 20, 28, 3))
                pygame.draw.rect(self.screen, self._color("grid_green"), pygame.Rect(sx - 14, sy - 20, int(28 * hp_ratio), 3))

        for orb in self.state.orbs:
            trail = list(orb.trail)
            if len(trail) > 1:
                for index in range(1, len(trail)):
                    fade = index / len(trail)
                    trail_color = self._color("orb_trail")
                    color = (*trail_color, int(150 * fade))
                    start = self._grid_to_screen(trail[index - 1][0], trail[index - 1][1])
                    end = self._grid_to_screen(trail[index][0], trail[index][1])
                    pygame.draw.line(self.glow_surface, color, start, end, self.visuals["orb_trail_width"] + 3)
                    pygame.draw.line(self.screen, trail_color, start, end, self.visuals["orb_trail_width"])
            sx, sy = self._grid_to_screen(orb.x, orb.y)
            head = self._color("orb_head")
            pygame.draw.circle(self.glow_surface, (*head, 180), (sx, sy), self.visuals["orb_head_radius"] + 5)
            pygame.draw.circle(self.screen, head, (sx, sy), self.visuals["orb_head_radius"])

        for enemy in self.state.enemies:
            sx, sy = self._grid_to_screen(enemy.x, enemy.y)
            enemy_color = self._color("enemy")
            pygame.draw.circle(self.glow_surface, (*enemy_color, 26), (sx, sy), self.visuals["enemy_radius"] + 3)
            pygame.draw.rect(self.screen, enemy_color, pygame.Rect(sx - 3, sy - 3, 6, 6), width=1)

    def _draw_hud(self) -> None:
        width, height = self.screen.get_size()
        self._draw_header(width)
        rail_x = width - 290
        rail = pygame.Rect(rail_x, 60, 250, height - 120)
        pygame.draw.rect(self.screen, (14, 16, 18), rail, width=1)
        y = rail.y + 18
        y = self._label("SYS.ID :: GRIDLINE", rail.x + 18, y, tone="muted")
        y = self._label("GRID::CTRL", rail.x + 18, y + 2, tone="bright", large=True)
        y = self._label(f"STATUS  ACTIVE", rail.right - 92, rail.y + 18, tone="green")
        y = self._draw_separator(rail.x + 18, y + 14, rail.width - 36)
        y = self._label(f"COINS   {self.state.coins}", rail.x + 18, y + 6, tone="muted")
        y = self._label(f"LEVEL   {self.state.level}", rail.x + 18, y, tone="muted")
        y = self._label(f"RED     {self.state.corruption_percent():05.1f}%", rail.x + 18, y, tone="red")
        y = self._label(f"ORBS    {len(self.state.orbs)}", rail.x + 18, y, tone="bright")
        y = self._label(f"FIRE/S  {self.state.shots_fired_this_second}", rail.x + 18, y, tone="green")
        y = self._draw_separator(rail.x + 18, y + 12, rail.width - 36)
        y = self._label("MODULES", rail.x + 18, y + 8, tone="muted")

        for tower in self.config.towers:
            label = f"{tower['display_name'].upper()}  ${tower['build_cost']}"
            rect = pygame.Rect(rail.x + 18, y + 4, rail.width - 36, 26)
            self._button(rect, label, f"tower:{tower['id']}", self.state.selected_tower_type_id == tower["id"])
            y += 34

        y = self._draw_separator(rail.x + 18, y + 8, rail.width - 36)
        y = self._label("UPGRADES", rail.x + 18, y + 10, tone="muted")
        state = self.state.tower_types[self.state.selected_tower_type_id]
        cooldown = self._selected_tower_cooldown()
        y = self._label(f"READY   {cooldown:04.2f}s", rail.x + 18, y + 2, tone="muted")
        for key in self.config.raw["upgrades"]["stats"]:
            cost = state.upgrade_cost(key, self.config.raw["upgrades"]["cost_curve_multiplier"])
            rect = pygame.Rect(rail.x + 18, y + 4, rail.width - 36, 22)
            self._button(rect, f"{key.upper():<16}${cost}", f"upgrade:{key}", False)
            y += 28

        y = self._draw_separator(rail.x + 18, y + 8, rail.width - 36)
        y = self._label("POWER", rail.x + 18, y + 10, tone="muted")
        self._button(
            pygame.Rect(rail.x + 18, y + 4, rail.width - 36, 24),
            f"FUND 10%  {self.state.power_tower.funding_percent:>3}%",
            "fund_power",
            False,
        )
        y += 30
        active = self.state.power_tower.active_time_remaining > 0
        charged = self.state.power_tower.charged
        label = "DEPLOY (P)" if charged else f"ACTIVE {self.state.power_tower.active_time_remaining:.1f}S" if active else "NOT CHARGED"
        self._button(pygame.Rect(rail.x + 18, y + 4, rail.width - 36, 24), label, "deploy_power", charged)
        self._draw_footer(width, height)

        if self.state.loss:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            text = self.font.render("Grid integrity failed", True, self._color("text"))
            self.screen.blit(text, text.get_rect(center=(width // 2, height // 2)))

    def _draw_header(self, width: int) -> None:
        self._label("SYS.ID :: 0X9281", 38, 38, tone="muted")
        self._label("GRIDLINE::CTRL", 38, 56, tone="bright", large=True)
        self._label("08 MODULES", 38, 82, tone="muted")
        self._draw_separator(38, 110, width - 76)

    def _draw_footer(self, width: int, height: int) -> None:
        self._draw_separator(38, height - 42, width - 76)
        self._label("status: live   // contain corruption", 52, height - 62, tone="amber")
        self._label("CORE  v0.2.1-alpha", 38, height - 28, tone="muted")
        self._label(f"UPTIME  {pygame.time.get_ticks() / 1000:07.2f}", width - 170, height - 28, tone="muted")

    def _button(self, rect: pygame.Rect, text: str, action: str, selected: bool) -> None:
        self.button_rects[action] = rect
        color = (16, 18, 20) if not selected else (24, 30, 34)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (68, 70, 72), rect, width=1)
        surface = self.small_font.render(text, True, self._color("text"))
        self.screen.blit(surface, (rect.x + 10, rect.y + 5))

    def _text(self, text: str, x: int, y: int, small: bool = False) -> int:
        font = self.small_font if small else self.font
        surface = font.render(text, True, self._color("text"))
        self.screen.blit(surface, (x, y))
        return y + surface.get_height() + 6

    def _label(self, text: str, x: int, y: int, tone: str = "muted", large: bool = False) -> int:
        font = self.font if large else self.small_font
        color = {
            "muted": (112, 112, 104),
            "bright": (214, 216, 210),
            "green": tuple(self._color("grid_green")),
            "amber": (176, 118, 72),
            "red": tuple(self._color("grid_red")),
        }[tone]
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))
        return y + surface.get_height()

    def _draw_separator(self, x: int, y: int, width: int) -> int:
        for offset in range(0, width, 8):
            pygame.draw.line(self.screen, (46, 42, 36), (x + offset, y), (x + offset + 3, y), 1)
        return y

    def _grid_base_color(self, tier: str) -> tuple[int, int, int]:
        if tier == "large":
            return (114, 86, 52)
        if tier == "medium":
            return (74, 60, 42)
        return (42, 34, 26)

    def _color(self, name: str) -> tuple[int, int, int]:
        return tuple(self.visuals["palette"][name])

    def _merge_visuals(self, visuals: dict) -> dict:
        merged = {
            "palette": dict(DEFAULT_VISUALS["palette"]),
            "grid_layer_width_by_tier": dict(DEFAULT_VISUALS["grid_layer_width_by_tier"]),
            "grid_layer_glow_alpha_by_tier": dict(DEFAULT_VISUALS["grid_layer_glow_alpha_by_tier"]),
            "orb_trail_width": DEFAULT_VISUALS["orb_trail_width"],
            "orb_head_radius": DEFAULT_VISUALS["orb_head_radius"],
            "enemy_radius": DEFAULT_VISUALS["enemy_radius"],
            "tower_radius": DEFAULT_VISUALS["tower_radius"],
            "grid_scale_multiplier": DEFAULT_VISUALS["grid_scale_multiplier"],
        }
        for key in ("palette", "grid_layer_width_by_tier", "grid_layer_glow_alpha_by_tier"):
            if key in visuals:
                merged[key].update(visuals[key])
        for key in ("orb_trail_width", "orb_head_radius", "enemy_radius", "tower_radius", "grid_scale_multiplier"):
            if key in visuals:
                merged[key] = visuals[key]
        return merged

    def _grid_to_screen(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(self.grid_origin[0] + x * self.cell_size),
            int(self.grid_origin[1] + y * self.cell_size),
        )

    def _update_layout(self) -> None:
        width, height = self.screen.get_size()
        left_margin = 38.0
        top_margin = 126.0
        bottom_margin = 74.0
        right_gap = 40.0
        available_width = width - self.sidebar_width - left_margin - right_gap
        available_height = height - top_margin - bottom_margin
        grid_width_units = max(1, self.state.grid_width - 1)
        grid_height_units = max(1, self.state.grid_height - 1)
        self.cell_size = min(available_width / grid_width_units, available_height / grid_height_units)
        self.cell_size *= self.visuals["grid_scale_multiplier"]
        play_width = grid_width_units * self.cell_size
        play_height = grid_height_units * self.cell_size
        origin_x = left_margin + max(0.0, (available_width - play_width) * 0.5)
        origin_y = top_margin + max(0.0, (available_height - play_height) * 0.5)
        self.grid_origin = (origin_x, origin_y)
        self.playfield_rect = pygame.Rect(
            int(origin_x - 18),
            int(origin_y - 18),
            int(play_width + 36),
            int(play_height + 36),
        )

    def _selected_tower_cooldown(self) -> float:
        cooldowns = [
            hardpoint.tower.cooldown
            for hardpoint in self.state.hardpoints
            if hardpoint.tower and hardpoint.tower.type_state.config["id"] == self.state.selected_tower_type_id
        ]
        return min(cooldowns) if cooldowns else 0.0


def main() -> int:
    config = load_game_config()
    GridlineApp(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
