from __future__ import annotations

import math
import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class SwordArena(BaseMicrogame):
    instruction = "Controller: Stick/D-Pad bewegen, A/X schlagen | Tastatur: WASD/Pfeile + Leertaste"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player = pygame.Vector2(SCREEN_W / 2, 500)
        self.speed = 330
        self.slash_timer = 0.0
        self.orbs: list[dict] = []
        starts = [(330, 330), (640, 410), (950, 320)]
        random.shuffle(starts)
        for choice, pos in zip(self.choices, starts):
            angle = random.uniform(0, math.tau)
            self.orbs.append({
                "choice": choice,
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(65, 105),
                "radius": 72,
            })

    def update(self, dt: float) -> None:
        move = self.controls.movement()
        if move.length_squared():
            self.player += move * self.speed * dt
        self.player.x = max(55, min(SCREEN_W - 55, self.player.x))
        self.player.y = max(PLAY_TOP + 55, min(SCREEN_H - 55, self.player.y))
        self.slash_timer = max(0.0, self.slash_timer - dt)

        if self.controls.pressed("action") and not self.done:
            self.slash_timer = 0.18
            for orb in self.orbs:
                if self.player.distance_to(orb["pos"]) <= orb["radius"] + 95:
                    self.choose(orb["choice"])
                    break

        for orb in self.orbs:
            orb["pos"] += orb["vel"] * dt
            r = orb["radius"]
            if orb["pos"].x < r or orb["pos"].x > SCREEN_W - r:
                orb["vel"].x *= -1
                orb["pos"].x = max(r, min(SCREEN_W - r, orb["pos"].x))
            if orb["pos"].y < PLAY_TOP + r or orb["pos"].y > SCREEN_H - r:
                orb["vel"].y *= -1
                orb["pos"].y = max(PLAY_TOP + r, min(SCREEN_H - r, orb["pos"].y))

    def draw(self) -> None:
        self.screen.fill(ui.BG)
        self.draw_common()
        pygame.draw.rect(self.screen, (24, 38, 42), pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP))
        for x in range(0, SCREEN_W, 80):
            pygame.draw.line(self.screen, (30, 49, 52), (x, PLAY_TOP), (x, SCREEN_H), 1)
        for y in range(PLAY_TOP, SCREEN_H, 80):
            pygame.draw.line(self.screen, (30, 49, 52), (0, y), (SCREEN_W, y), 1)

        answer_font = ui.font(21, True)
        for orb in self.orbs:
            pos = (int(orb["pos"].x), int(orb["pos"].y))
            pygame.draw.circle(self.screen, (52, 72, 95), pos, orb["radius"])
            pygame.draw.circle(self.screen, ui.ACCENT_2, pos, orb["radius"], 3)
            rect = pygame.Rect(pos[0] - 60, pos[1] - 40, 120, 85)
            ui.draw_wrapped(self.screen, orb["choice"].text, answer_font, ui.TEXT, rect, center=True, line_gap=2)

        p = (int(self.player.x), int(self.player.y))
        pygame.draw.circle(self.screen, ui.ACCENT, p, 26)
        pygame.draw.circle(self.screen, ui.TEXT, p, 26, 3)
        sword_end = (p[0] + 45, p[1] - 32)
        pygame.draw.line(self.screen, ui.TEXT, p, sword_end, 7)
        pygame.draw.line(self.screen, ui.GOLD, sword_end, (sword_end[0] + 22, sword_end[1] - 15), 5)
        if self.slash_timer > 0:
            pygame.draw.circle(self.screen, ui.GOLD, p, 95, 6)
