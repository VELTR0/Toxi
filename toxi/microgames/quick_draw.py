from __future__ import annotations

import math
import random

import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class QuickDraw(BaseMicrogame):
    """Aim a free-moving crosshair and shoot the chosen answer."""

    CURSOR_SPEED = 560
    SHOT_TIME = 0.24

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.crosshair = pygame.Vector2(SCREEN_W / 2, 440)
        self.shot_timer = 0.0
        self.shot_pos = self.crosshair.copy()
        self.shot_choice = None
        self.shot_index: int | None = None
        self.miss_marks: list[pygame.Vector2] = []

        self.answer_font = ui.font(18, True)
        self.answers: list[tuple[object, pygame.Rect]] = []

        # One randomized position per screen region keeps all three answers well
        # distributed without ever letting adaptive answer boxes overlap.
        columns = [
            [(235, 315), (270, 505)],
            [(640, 305), (640, 520)],
            [(1045, 330), (1010, 500)],
        ]
        positions = [random.choice(column) for column in columns]
        random.shuffle(positions)

        for choice, center in zip(self.choices, positions):
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.answer_font,
                min_width=200,
                max_width=320,
                min_height=76,
                padding_x=18,
                padding_y=13,
                line_gap=2,
            )
            rect = pygame.Rect(0, 0, width, height)
            rect.center = center
            self.answers.append((choice, rect))

    def _fire(self) -> None:
        if self.done or self.shot_timer > 0.0:
            return

        self.shot_pos = self.crosshair.copy()
        self.shot_choice = None
        self.shot_index = None

        for index, (choice, rect) in enumerate(self.answers):
            if rect.collidepoint(self.shot_pos.x, self.shot_pos.y):
                self.shot_choice = choice
                self.shot_index = index
                break

        if self.shot_choice is None:
            self.miss_marks.append(self.shot_pos.copy())
            self.miss_marks = self.miss_marks[-8:]

        self.shot_timer = self.SHOT_TIME

    def update(self, dt: float) -> None:
        if self.shot_timer > 0.0:
            self.shot_timer = max(0.0, self.shot_timer - dt)
            if self.shot_timer <= 0.0:
                if self.shot_choice is not None:
                    self.choose(self.shot_choice)
                else:
                    self.shot_index = None
            return

        move = self.controls.movement()
        if move.length_squared():
            self.crosshair += move * self.CURSOR_SPEED * dt

        margin = 28
        self.crosshair.x = max(margin, min(SCREEN_W - margin, self.crosshair.x))
        self.crosshair.y = max(PLAY_TOP + margin, min(SCREEN_H - margin, self.crosshair.y))

        if self.controls.pressed("action") or self.controls.pressed("confirm"):
            self._fire()

    def _targeted_index(self) -> int | None:
        for index, (_, rect) in enumerate(self.answers):
            if rect.collidepoint(self.crosshair.x, self.crosshair.y):
                return index
        return None

    def _draw_crosshair(self) -> None:
        pos = self.shot_pos if self.shot_timer > 0.0 else self.crosshair
        x, y = int(pos.x), int(pos.y)
        targeted = self._targeted_index() is not None
        color = ui.GOLD if targeted else ui.TEXT

        recoil = 0
        if self.shot_timer > 0.0:
            progress = 1.0 - self.shot_timer / self.SHOT_TIME
            recoil = int(math.sin(progress * math.pi) * 15)
            color = ui.DANGER

        radius = 22 + recoil
        pygame.draw.circle(self.screen, color, (x, y), radius, 3)
        pygame.draw.circle(self.screen, color, (x, y), 4, 2)
        pygame.draw.line(self.screen, color, (x - radius - 12, y), (x - 8, y), 3)
        pygame.draw.line(self.screen, color, (x + 8, y), (x + radius + 12, y), 3)
        pygame.draw.line(self.screen, color, (x, y - radius - 12), (x, y - 8), 3)
        pygame.draw.line(self.screen, color, (x, y + 8), (x, y + radius + 12), 3)

    def _draw_shot_animation(self) -> None:
        if self.shot_timer <= 0.0:
            return

        progress = 1.0 - self.shot_timer / self.SHOT_TIME
        x, y = int(self.shot_pos.x), int(self.shot_pos.y)

        # Brief screen flash plus an expanding eight-point impact burst makes a
        # shot readable even when it misses every answer.
        flash_strength = max(0, 105 - int(progress * 260))
        if flash_strength:
            flash = pygame.Surface((SCREEN_W, SCREEN_H - PLAY_TOP), pygame.SRCALPHA)
            flash.fill((255, 232, 176, flash_strength))
            self.screen.blit(flash, (0, PLAY_TOP))

        burst = int(18 + progress * 52)
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            inner = 9
            start = (x + int(math.cos(radians) * inner), y + int(math.sin(radians) * inner))
            end = (x + int(math.cos(radians) * burst), y + int(math.sin(radians) * burst))
            pygame.draw.line(self.screen, ui.GOLD, start, end, 4)

        pygame.draw.circle(self.screen, ui.TEXT, (x, y), max(3, 8 - int(progress * 5)))

    def draw(self) -> None:
        self.screen.fill((22, 19, 24))
        self.draw_common()

        arena = pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP)
        pygame.draw.rect(self.screen, (74, 52, 43), arena)

        # Original procedural shooting-gallery scenery; no external game assets.
        pygame.draw.rect(self.screen, (92, 64, 49), pygame.Rect(0, 585, SCREEN_W, 135))
        for y in range(PLAY_TOP + 35, SCREEN_H, 58):
            pygame.draw.line(self.screen, (84, 59, 47), (0, y), (SCREEN_W, y), 2)
        for x in range(0, SCREEN_W, 160):
            pygame.draw.line(self.screen, (63, 45, 40), (x, PLAY_TOP), (x, SCREEN_H), 2)

        # Permanent small marks make empty shots visible without affecting play.
        for mark in self.miss_marks:
            p = (int(mark.x), int(mark.y))
            pygame.draw.circle(self.screen, (38, 30, 31), p, 7)
            pygame.draw.circle(self.screen, (151, 113, 78), p, 7, 2)

        for index, (choice, rect) in enumerate(self.answers):
            targeted = index == self._targeted_index()
            hit_flash = self.shot_timer > 0.0 and index == self.shot_index
            fill = (72, 60, 57) if not targeted else (88, 70, 58)
            border = ui.DANGER if hit_flash else (ui.GOLD if targeted else ui.ACCENT_2)
            pygame.draw.rect(self.screen, (38, 31, 34), rect.move(7, 7), border_radius=13)
            pygame.draw.rect(self.screen, fill, rect, border_radius=13)
            pygame.draw.rect(self.screen, border, rect, 4 if targeted or hit_flash else 3, border_radius=13)
            ui.draw_wrapped(
                self.screen,
                choice.text,
                self.answer_font,
                ui.TEXT,
                rect.inflate(-22, -16),
                center=True,
                vertical_center=True,
                line_gap=2,
            )

        self._draw_shot_animation()
        self._draw_crosshair()
