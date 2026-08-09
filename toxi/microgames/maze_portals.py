from __future__ import annotations

import math
import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W

class MazePortals(BaseMicrogame):
    instruction = "WASD/Pfeile: durch das Labor laufen | Betritt das richtige Portal"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player = pygame.Vector2(640, 650)
        self.speed = 310
        self.size = 34
        self.walls = [
            pygame.Rect(210, 350, 350, 28),
            pygame.Rect(720, 350, 350, 28),
            pygame.Rect(460, 500, 360, 28),
        ]
        xs = [190, 515, 840]
        self.portals = []
        for choice, x in zip(self.choices, xs):
            self.portals.append((choice, pygame.Rect(x, 215, 250, 105)))

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
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if move.length_squared():
            move = move.normalize() * self.speed * dt
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
        answer_font = ui.font(20, True)
        for choice, portal in self.portals:
            pygame.draw.rect(self.screen, (46, 65, 94), portal, border_radius=18)
            pygame.draw.rect(self.screen, ui.ACCENT_2, portal, 4, border_radius=18)
            ui.draw_wrapped(self.screen, choice.text, answer_font, ui.TEXT, portal.inflate(-18, -18), center=True, line_gap=2)
        for wall in self.walls:
            pygame.draw.rect(self.screen, (76, 88, 109), wall, border_radius=8)
            for x in range(wall.left + 15, wall.right, 38):
                pygame.draw.circle(self.screen, ui.MUTED, (x, wall.centery), 4)
        p = (int(self.player.x), int(self.player.y))
        pygame.draw.circle(self.screen, ui.ACCENT, p, 22)
        pygame.draw.circle(self.screen, ui.TEXT, p, 22, 3)
        pygame.draw.circle(self.screen, ui.DANGER, (p[0] + 7, p[1] - 4), 5)
