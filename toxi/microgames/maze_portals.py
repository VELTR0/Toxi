from __future__ import annotations

import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class MazePortals(BaseMicrogame):
    instruction = "Controller: Stick/D-Pad durch das Labor | Tastatur: WASD/Pfeile | Betritt das richtige Portal"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player = pygame.Vector2(640, 650)
        self.speed = 310
        self.size = 34
        self.answer_font = ui.font(20, True)

        centers = [215, 640, 1065]
        self.portals = []
        for choice, center_x in zip(self.choices, centers):
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.answer_font,
                min_width=200,
                max_width=330,
                min_height=86,
                padding_x=20,
                padding_y=14,
                line_gap=2,
            )
            portal = pygame.Rect(0, 0, width, height)
            portal.midtop = (center_x, 205)
            self.portals.append((choice, portal))

        self.walls = self._generate_walls()

    def _generate_walls(self) -> list[pygame.Rect]:
        """Create three randomized, guaranteed-solvable barrier rows.

        Each horizontal row has one generous opening. The gap positions are
        chosen almost independently across the full arena and are encouraged to
        be far apart, producing much stronger left/right variation between rows.
        """
        walls: list[pygame.Rect] = []
        thickness = random.randint(24, 30)

        # Exactly three rows. The former highest/fourth layer was removed so the
        # area below the three answer portals stays more open.
        row_bases = [430, 510, 590]
        row_ys = sorted(base + random.randint(-12, 12) for base in row_bases)

        previous_center: int | None = None
        for y in row_ys:
            gap_width = random.randint(175, 235)
            margin = gap_width // 2 + 55

            # Pick each opening from almost the whole screen. If possible, keep
            # it well away from the previous opening so successive passages do
            # not keep clustering in the same area.
            gap_center = random.randint(margin, SCREEN_W - margin)
            if previous_center is not None:
                for _ in range(12):
                    candidate = random.randint(margin, SCREEN_W - margin)
                    if abs(candidate - previous_center) >= 300:
                        gap_center = candidate
                        break
                    gap_center = candidate

            previous_center = gap_center
            gap_left = int(gap_center - gap_width / 2)
            gap_right = int(gap_center + gap_width / 2)

            if gap_left > 0:
                walls.append(pygame.Rect(0, y, gap_left, thickness))
            if gap_right < SCREEN_W:
                walls.append(pygame.Rect(gap_right, y, SCREEN_W - gap_right, thickness))

        return walls

    def _move_axis(self, delta: pygame.Vector2) -> None:
        if delta.x:
            self.player.x += delta.x
            rect = pygame.Rect(0, 0, self.size, self.size)
            rect.center = self.player
            for wall in self.walls:
                if rect.colliderect(wall):
                    if delta.x > 0:
                        rect.right = wall.left
                    else:
                        rect.left = wall.right
                    self.player.x = rect.centerx
        if delta.y:
            self.player.y += delta.y
            rect = pygame.Rect(0, 0, self.size, self.size)
            rect.center = self.player
            for wall in self.walls:
                if rect.colliderect(wall):
                    if delta.y > 0:
                        rect.bottom = wall.top
                    else:
                        rect.top = wall.bottom
                    self.player.y = rect.centery

    def update(self, dt: float) -> None:
        move = self.controls.movement()
        if move.length_squared():
            move *= self.speed * dt
            self._move_axis(pygame.Vector2(move.x, 0))
            self._move_axis(pygame.Vector2(0, move.y))
        self.player.x = max(self.size / 2, min(SCREEN_W - self.size / 2, self.player.x))
        self.player.y = max(PLAY_TOP + self.size / 2, min(SCREEN_H - self.size / 2, self.player.y))

        p_rect = pygame.Rect(0, 0, self.size, self.size)
        p_rect.center = self.player
        for choice, portal in self.portals:
            if p_rect.colliderect(portal):
                self.choose(choice)
                break

    def draw(self) -> None:
        self.screen.fill(ui.BG)
        self.draw_common()
        pygame.draw.rect(self.screen, (25, 31, 49), pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP))
        for choice, portal in self.portals:
            pygame.draw.rect(self.screen, (46, 65, 94), portal, border_radius=18)
            pygame.draw.rect(self.screen, ui.ACCENT_2, portal, 4, border_radius=18)
            ui.draw_wrapped(
                self.screen,
                choice.text,
                self.answer_font,
                ui.TEXT,
                portal.inflate(-28, -20),
                center=True,
                line_gap=2,
                vertical_center=True,
            )
        for wall in self.walls:
            pygame.draw.rect(self.screen, (76, 88, 109), wall, border_radius=8)
            for x in range(wall.left + 15, wall.right, 38):
                pygame.draw.circle(self.screen, ui.MUTED, (x, wall.centery), 4)
        p = (int(self.player.x), int(self.player.y))
        pygame.draw.circle(self.screen, ui.ACCENT, p, 22)
        pygame.draw.circle(self.screen, ui.TEXT, p, 22, 3)
        pygame.draw.circle(self.screen, ui.DANGER, (p[0] + 7, p[1] - 4), 5)
