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
        self.answer_font = ui.font(18, True)
        self.items: list[dict] = []
        xs = [220, 640, 1060]
        fall_time_multiplier = 1.5
        for choice, x in zip(self.choices, xs):
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.answer_font,
                min_width=180,
                max_width=300,
                min_height=68,
                padding_x=20,
                padding_y=12,
                line_gap=1,
            )
            self.items.append({
                "choice": choice,
                "pos": pygame.Vector2(x, random.uniform(225, 330)),
                "speed": random.uniform(70, 105) / fall_time_multiplier,
                "phase": random.uniform(0, math.tau),
                "size": (width, height),
            })
        self.elapsed = 0.0

    @staticmethod
    def _item_rect(item: dict) -> pygame.Rect:
        rect = pygame.Rect(0, 0, item["size"][0], item["size"][1])
        rect.center = item["pos"]
        return rect

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.basket_x += self.controls.move_x * self.speed * dt
        self.basket_x = max(100, min(SCREEN_W - 100, self.basket_x))
        basket = pygame.Rect(int(self.basket_x - 90), 645, 180, 50)

        for item in self.items:
            item["pos"].y += item["speed"] * dt
            item["pos"].x += math.sin(self.elapsed * 1.6 + item["phase"]) * 25 * dt
            rect = self._item_rect(item)
            if rect.colliderect(basket):
                self.choose(item["choice"])
                return
            if rect.top > SCREEN_H:
                width = item["size"][0]
                item["pos"].y = 215
                item["pos"].x = random.randint(width // 2 + 20, SCREEN_W - width // 2 - 20)

    def draw(self) -> None:
        self.screen.fill(ui.BG)
        self.draw_common()
        pygame.draw.rect(self.screen, (22, 38, 48), pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP))
        for x in range(70, SCREEN_W, 130):
            pygame.draw.line(self.screen, (37, 62, 69), (x, PLAY_TOP), (x, SCREEN_H), 2)
        for item in self.items:
            rect = self._item_rect(item)
            radius = min(32, rect.height // 2)
            pygame.draw.rect(self.screen, (48, 72, 86), rect, border_radius=radius)
            pygame.draw.rect(self.screen, ui.ACCENT, rect, 3, border_radius=radius)
            ui.draw_wrapped(
                self.screen,
                item["choice"].text,
                self.answer_font,
                ui.TEXT,
                rect.inflate(-28, -18),
                center=True,
                line_gap=1,
                vertical_center=True,
            )
        basket = pygame.Rect(int(self.basket_x - 90), 645, 180, 50)
        pygame.draw.rect(self.screen, ui.GOLD, basket, 5, border_radius=12)
        pygame.draw.line(self.screen, ui.GOLD, (basket.left + 20, basket.bottom), (basket.right - 20, basket.bottom), 8)
