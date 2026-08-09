from __future__ import annotations

import math
import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class CometClick(BaseMicrogame):
    instruction = "Controller: D-Pad/Stick auswählen, A bestätigen | Maus: Komet anklicken"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.elapsed = 0.0
        self.selected = 0
        self.answer_font = ui.font(19, True)
        centers = [pygame.Vector2(250, 420), pygame.Vector2(640, 500), pygame.Vector2(1030, 390)]
        self.comets = []
        for choice, center in zip(self.choices, centers):
            radius = ui.adaptive_circle_radius(
                choice.text,
                self.answer_font,
                min_radius=62,
                max_radius=124,
                padding=10,
                line_gap=1,
            )
            self.comets.append({
                "choice": choice,
                "base": center,
                "pos": center.copy(),
                "phase": random.uniform(0, math.tau),
                "radius": radius,
            })

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = pygame.Vector2(event.pos)
            for comet in self.comets:
                if mouse.distance_to(comet["pos"]) < comet["radius"]:
                    self.choose(comet["choice"])
                    break

    def update(self, dt: float) -> None:
        self.elapsed += dt
        for comet in self.comets:
            comet["pos"].x = comet["base"].x + math.sin(self.elapsed * 1.1 + comet["phase"]) * 55
            comet["pos"].y = comet["base"].y + math.cos(self.elapsed * 0.9 + comet["phase"]) * 35

        if self.controls.pressed("left") or self.controls.pressed("up"):
            self.selected = (self.selected - 1) % len(self.comets)
        elif self.controls.pressed("right") or self.controls.pressed("down"):
            self.selected = (self.selected + 1) % len(self.comets)

        if (self.controls.pressed("confirm") or self.controls.pressed("action")) and not self.done:
            self.choose(self.comets[self.selected]["choice"])

    def draw(self) -> None:
        self.screen.fill((10, 18, 26))
        self.draw_common()
        for i in range(85):
            x = (i * 149) % SCREEN_W
            y = PLAY_TOP + ((i * 83) % (SCREEN_H - PLAY_TOP))
            pygame.draw.circle(self.screen, (53, 72, 88), (x, y), 1)

        for index, comet in enumerate(self.comets):
            x, y = int(comet["pos"].x), int(comet["pos"].y)
            radius = comet["radius"]
            trail = [
                (int(radius * 1.55), max(8, int(radius * 0.18))),
                (int(radius * 1.15), max(10, int(radius * 0.24))),
                (int(radius * 0.78), max(13, int(radius * 0.32))),
            ]
            for offset, trail_radius in trail:
                pygame.draw.circle(
                    self.screen,
                    (40, 100, 100),
                    (x - offset, y + offset // 5),
                    trail_radius,
                )
            pygame.draw.circle(self.screen, ui.ACCENT, (x, y), radius)
            pygame.draw.circle(self.screen, (213, 255, 240), (x, y), radius, 3)
            if index == self.selected:
                pygame.draw.circle(self.screen, ui.GOLD, (x, y), radius + 16, 5)
                marker = ui.font(18, True).render("A", True, ui.GOLD)
                self.screen.blit(marker, marker.get_rect(center=(x, y - radius - 30)))

            inner = int(radius * 1.4) - 16
            rect = pygame.Rect(0, 0, inner, inner)
            rect.center = (x, y)
            ui.draw_wrapped(
                self.screen,
                comet["choice"].text,
                self.answer_font,
                ui.TEXT,
                rect,
                center=True,
                line_gap=1,
                vertical_center=True,
            )
