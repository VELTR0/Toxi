from __future__ import annotations

import math
from pathlib import Path

import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class SoleMan(BaseMicrogame):
    """Move the leg sprite horizontally and stomp the chosen answer."""

    MOVE_SPEED = 520
    STOMP_DOWN_TIME = 0.16
    CRUSH_TIME = 0.38
    RETURN_TIME = 0.24
    STOMP_DISTANCE = 255

    FOOT_MAX_W = 220
    FOOT_MAX_H = 250
    SOLE_HITBOX_HEIGHT_RATIO = 0.28
    SOLE_HITBOX_WIDTH_RATIO = 0.86

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.foot_sprite = self._load_foot_sprite()
        self.foot_x = SCREEN_W / 2
        self.hover_y = 205.0
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

    def _load_foot_sprite(self) -> pygame.Surface:
        asset_path = Path(__file__).resolve().parents[2] / "ressources" / "sprites" / "leg.png"
        image = pygame.image.load(str(asset_path)).convert_alpha()
        width, height = image.get_size()
        scale = min(self.FOOT_MAX_W / width, self.FOOT_MAX_H / height)
        target_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        return pygame.transform.smoothscale(image, target_size)

    def _stomp_offset(self) -> float:
        if self.phase == "stomp_down":
            progress = 1.0 - self.phase_timer / self.STOMP_DOWN_TIME
            return self.STOMP_DISTANCE * math.sqrt(max(0.0, min(1.0, progress)))
        if self.phase == "crush":
            return self.impact_offset
        if self.phase == "return":
            progress = 1.0 - self.phase_timer / self.RETURN_TIME
            return self.impact_offset * (1.0 - progress)
        return 0.0

    def _foot_rect(self, offset: float | None = None) -> pygame.Rect:
        if offset is None:
            offset = self._stomp_offset()
        rect = self.foot_sprite.get_rect()
        rect.midtop = (int(self.foot_x), int(self.hover_y + offset))
        return rect

    def _sole_hitbox(self, offset: float | None = None) -> pygame.Rect:
        sprite_rect = self._foot_rect(offset)
        width = max(60, int(sprite_rect.width * self.SOLE_HITBOX_WIDTH_RATIO))
        height = max(26, int(sprite_rect.height * self.SOLE_HITBOX_HEIGHT_RATIO))
        hitbox = pygame.Rect(0, 0, width, height)
        hitbox.midbottom = sprite_rect.midbottom
        return hitbox

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
            half = self.foot_sprite.get_width() / 2 + 8
            self.foot_x = max(half, min(SCREEN_W - half, self.foot_x))
            if self.controls.pressed("action") or self.controls.pressed("confirm"):
                self._begin_stomp()
            return

        previous_offset = self._stomp_offset()
        self.phase_timer = max(0.0, self.phase_timer - dt)

        if self.phase == "stomp_down":
            offset = self._stomp_offset()
            previous_sole = self._sole_hitbox(previous_offset)
            sole = self._sole_hitbox(offset)
            swept_sole = previous_sole.union(sole)

            for index, (choice, rect) in enumerate(self.answers):
                if swept_sole.colliderect(rect):
                    overshoot = max(0, sole.bottom - rect.top)
                    self.impact_offset = max(0.0, offset - overshoot + 8)
                    self.crushed_choice = choice
                    self.crushed_index = index
                    self.phase = "crush"
                    self.phase_timer = self.CRUSH_TIME
                    return

            if self.phase_timer <= 0.0:
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

    def draw(self) -> None:
        self.screen.fill((19, 22, 35))
        self.draw_common()

        arena = pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP)
        pygame.draw.rect(self.screen, (31, 38, 55), arena)
        pygame.draw.rect(self.screen, (47, 52, 67), pygame.Rect(0, 655, SCREEN_W, 65))
        for x in range(0, SCREEN_W, 96):
            pygame.draw.line(self.screen, (55, 62, 78), (x, 655), (x + 42, SCREEN_H), 2)

        for index, (choice, rect) in enumerate(self.answers):
            self._draw_answer(index, choice, rect)

        foot_rect = self._foot_rect()
        self.screen.blit(self.foot_sprite, foot_rect)

        if self.phase == "crush":
            progress = 1.0 - self.phase_timer / self.CRUSH_TIME
            radius = int(18 + progress * 38)
            alpha = max(0, 170 - int(progress * 170))
            dust = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(dust, (214, 197, 166, alpha), (radius + 4, radius + 4), radius, 3)
            sole = self._sole_hitbox()
            self.screen.blit(dust, dust.get_rect(center=(sole.centerx, sole.bottom - 4)))
