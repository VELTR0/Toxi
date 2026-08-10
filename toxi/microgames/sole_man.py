from __future__ import annotations

import math

import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class SoleMan(BaseMicrogame):
    """Move a simple two-rectangle foot and stomp the chosen answer."""

    MOVE_SPEED = 520
    STOMP_DOWN_TIME = 0.16
    CRUSH_TIME = 0.38
    RETURN_TIME = 0.24
    STOMP_DISTANCE = 255

    LEG_W = 58
    LEG_H = 104
    SOLE_W = 132
    SOLE_H = 46

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.foot_x = SCREEN_W / 2
        self.hover_y = 235.0
        self.phase = "hover"
        self.phase_timer = 0.0
        self.impact_offset = 0.0
        self.crushed_choice = None
        self.crushed_index: int | None = None

        self.answer_font = ui.font(18, True)
        self.answers: list[tuple[object, pygame.Rect]] = []
        centers = [220, 640, 1060]
        for choice, center_x in zip(self.choices, centers):
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.answer_font,
                min_width=220,
                max_width=340,
                min_height=76,
                padding_x=20,
                padding_y=14,
                line_gap=2,
            )
            rect = pygame.Rect(0, 0, width, height)
            rect.midbottom = (center_x, 655)
            self.answers.append((choice, rect))

    def _stomp_offset(self) -> float:
        if self.phase == "stomp_down":
            progress = 1.0 - self.phase_timer / self.STOMP_DOWN_TIME
            # Fast initial drop, then a tiny ease into the target.
            return self.STOMP_DISTANCE * math.sqrt(max(0.0, min(1.0, progress)))
        if self.phase == "crush":
            return self.impact_offset
        if self.phase == "return":
            progress = 1.0 - self.phase_timer / self.RETURN_TIME
            return self.impact_offset * (1.0 - progress)
        return 0.0

    def _foot_rects(self, offset: float | None = None) -> tuple[pygame.Rect, pygame.Rect]:
        if offset is None:
            offset = self._stomp_offset()
        y = int(self.hover_y + offset)
        x = int(self.foot_x)
        leg = pygame.Rect(0, 0, self.LEG_W, self.LEG_H)
        leg.midtop = (x, y)
        sole = pygame.Rect(0, 0, self.SOLE_W, self.SOLE_H)
        sole.midtop = (x, y + self.LEG_H - 18)
        return leg, sole

    def _begin_stomp(self) -> None:
        if self.phase != "hover" or self.done:
            return
        self.phase = "stomp_down"
        self.phase_timer = self.STOMP_DOWN_TIME
        self.crushed_choice = None
        self.crushed_index = None
        self.impact_offset = 0.0

    def update(self, dt: float) -> None:
        if self.phase == "hover":
            self.foot_x += self.controls.move_x * self.MOVE_SPEED * dt
            half = self.SOLE_W / 2 + 8
            self.foot_x = max(half, min(SCREEN_W - half, self.foot_x))
            if self.controls.pressed("action") or self.controls.pressed("confirm"):
                self._begin_stomp()
            return

        self.phase_timer = max(0.0, self.phase_timer - dt)

        if self.phase == "stomp_down":
            offset = self._stomp_offset()
            _, sole = self._foot_rects(offset)
            for index, (choice, rect) in enumerate(self.answers):
                if sole.colliderect(rect):
                    self.crushed_choice = choice
                    self.crushed_index = index
                    self.impact_offset = offset
                    self.phase = "crush"
                    self.phase_timer = self.CRUSH_TIME
                    return

            if self.phase_timer <= 0.0:
                # A stomp between answers is a harmless miss. Return to the
                # hover position so the player can aim again.
                self.impact_offset = self.STOMP_DISTANCE
                self.phase = "return"
                self.phase_timer = self.RETURN_TIME
            return

        if self.phase == "crush":
            if self.phase_timer <= 0.0 and self.crushed_choice is not None:
                self.choose(self.crushed_choice)
            return

        if self.phase == "return" and self.phase_timer <= 0.0:
            self.phase = "hover"
            self.impact_offset = 0.0

    def _draw_answer(self, index: int, choice, rect: pygame.Rect) -> None:
        if self.phase == "crush" and index == self.crushed_index:
            progress = 1.0 - self.phase_timer / self.CRUSH_TIME
            squish = max(0.14, 1.0 - progress * 0.86)
            crushed = rect.copy()
            crushed.height = max(12, int(rect.height * squish))
            crushed.width = min(int(rect.width * (1.0 + 0.12 * progress)), 370)
            crushed.midbottom = rect.midbottom
            pygame.draw.rect(self.screen, (78, 57, 72), crushed, border_radius=12)
            pygame.draw.rect(self.screen, ui.GOLD, crushed, 3, border_radius=12)
            if progress < 0.35:
                ui.draw_wrapped(
                    self.screen,
                    choice.text,
                    self.answer_font,
                    ui.TEXT,
                    crushed.inflate(-18, -8),
                    center=True,
                    vertical_center=True,
                    line_gap=2,
                )
            return

        pygame.draw.rect(self.screen, (47, 59, 82), rect, border_radius=14)
        pygame.draw.rect(self.screen, ui.ACCENT_2, rect, 3, border_radius=14)
        ui.draw_wrapped(
            self.screen,
            choice.text,
            self.answer_font,
            ui.TEXT,
            rect.inflate(-18, -12),
            center=True,
            vertical_center=True,
            line_gap=2,
        )

    def _draw_prompt(self) -> None:
        panel = pygame.Rect(30, 205, 330, 62)
        ui.draw_panel(self.screen, panel, color=(37, 44, 62), radius=14)
        ui.draw_wrapped(
            self.screen,
            "Zerstampfe die Antwort!",
            ui.font(21, True),
            ui.TEXT,
            panel.inflate(-18, -10),
            center=True,
            vertical_center=True,
            line_gap=2,
        )

    def draw(self) -> None:
        self.screen.fill((19, 22, 35))
        self.draw_common()

        arena = pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP)
        pygame.draw.rect(self.screen, (31, 38, 55), arena)
        pygame.draw.rect(self.screen, (47, 52, 67), pygame.Rect(0, 655, SCREEN_W, 65))
        for x in range(0, SCREEN_W, 96):
            pygame.draw.line(self.screen, (55, 62, 78), (x, 655), (x + 42, SCREEN_H), 2)

        self._draw_prompt()

        for index, (choice, rect) in enumerate(self.answers):
            self._draw_answer(index, choice, rect)

        leg, sole = self._foot_rects()
        pygame.draw.rect(self.screen, (236, 184, 135), leg, border_radius=16)
        pygame.draw.rect(self.screen, (255, 213, 164), sole, border_radius=18)
        pygame.draw.rect(self.screen, ui.TEXT, leg, 3, border_radius=16)
        pygame.draw.rect(self.screen, ui.TEXT, sole, 3, border_radius=18)

        # A few toe marks keep the two-rectangle foot readable without sprites.
        for i in range(4):
            toe_x = sole.left + 22 + i * 24
            pygame.draw.line(
                self.screen,
                (188, 135, 106),
                (toe_x, sole.top + 8),
                (toe_x + 8, sole.top + 15),
                3,
            )

        if self.phase == "crush":
            progress = 1.0 - self.phase_timer / self.CRUSH_TIME
            radius = int(18 + progress * 38)
            alpha = max(0, 170 - int(progress * 170))
            dust = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(dust, (214, 197, 166, alpha), (radius + 4, radius + 4), radius, 3)
            self.screen.blit(dust, dust.get_rect(center=(sole.centerx, sole.bottom - 4)))
