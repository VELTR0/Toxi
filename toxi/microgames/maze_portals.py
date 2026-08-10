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
        """Create a fresh, guaranteed-solvable maze for every round.

        The maze consists of several full-width barrier rows with one generous
        opening in each row. The openings wander left and right as the player
        moves upward, producing a different zig-zag route every time while
        always preserving a path from the spawn area to all three portals.
        """
        walls: list[pygame.Rect] = []
        thickness = random.randint(24, 30)

        # Portal boxes can extend down to roughly y=330. Keeping the highest
        # barrier below that leaves the whole answer row freely reachable once
        # the player has crossed the maze.
        row_count = random.choice((3, 4))
        row_bases = [360, 435, 510, 585]
        if row_count == 3:
            row_bases = random.sample(row_bases, 3)
        row_ys = sorted(base + random.randint(-10, 10) for base in row_bases)

        gap_center = random.randint(250, SCREEN_W - 250)
        for y in row_ys:
            gap_width = random.randint(185, 245)

            # Make the route meander, but do not teleport the next opening to
            # the opposite side of the screen. This keeps the maze readable and
            # avoids long empty traversals between neighboring rows.
            gap_center += random.randint(-285, 285)
            gap_center = max(gap_width // 2 + 70, min(SCREEN_W - gap_width // 2 - 70, gap_center))

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
