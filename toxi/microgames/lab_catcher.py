from __future__ import annotations

import math
import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class LabCatcher(BaseMicrogame):
    instruction = "Controller: Stick/D-Pad links/rechts | Tastatur: A/D/Pfeile | Fange die richtige Antwort"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.basket_x = SCREEN_W / 2
        self.speed = 430
        self.items: list[dict] = []
        xs = [250, 640, 1030]
        fall_time_multiplier = 1.5
        for choice, x in zip(self.choices, xs):
            self.items.append({
                "choice": choice,
                "pos": pygame.Vector2(x, random.uniform(225, 340)),
                # 1.5x fall time means 2/3 of the previous falling speed.
                "speed": random.uniform(70, 105) / fall_time_multiplier,
                "phase": random.uniform(0, math.tau),
            })
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.basket_x += self.controls.move_x * self.speed * dt
        self.basket_x = max(100, min(SCREEN_W - 100, self.basket_x))
        basket = pygame.Rect(int(self.basket_x - 90), 645, 180, 50)

        for item in self.items:
            item["pos"].y += item["speed"] * dt
            item["pos"].x += math.sin(self.elapsed * 1.6 + item["phase"]) * 25 * dt
            rect = pygame.Rect(0, 0, 220, 72)
            rect.center = item["pos"]
            if rect.colliderect(basket):
                self.choose(item["choice"])
                return
            if rect.top > SCREEN_H:
                item["pos"].y = 215
                item["pos"].x = random.randint(180, SCREEN_W - 180)

    def draw(self) -> None:
        self.screen.fill(ui.BG)
        self.draw_common()
        pygame.draw.rect(self.screen, (22, 38, 48), pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP))
        for x in range(70, SCREEN_W, 130):
            pygame.draw.line(self.screen, (37, 62, 69), (x, PLAY_TOP), (x, SCREEN_H), 2)
        answer_font = ui.font(18, True)
        for item in self.items:
            rect = pygame.Rect(0, 0, 220, 72)
            rect.center = item["pos"]
            pygame.draw.rect(self.screen, (48, 72, 86), rect, border_radius=32)
            pygame.draw.rect(self.screen, ui.ACCENT, rect, 3, border_radius=32)
            ui.draw_wrapped(self.screen, item["choice"].text, answer_font, ui.TEXT, rect.inflate(-18, -12), center=True, line_gap=0)
        basket = pygame.Rect(int(self.basket_x - 90), 645, 180, 50)
        pygame.draw.rect(self.screen, ui.GOLD, basket, 5, border_radius=12)
        pygame.draw.line(self.screen, ui.GOLD, (basket.left + 20, basket.bottom), (basket.right - 20, basket.bottom), 8)
