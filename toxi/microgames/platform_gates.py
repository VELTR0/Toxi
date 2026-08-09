from __future__ import annotations

import random

import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class PlatformGates(BaseMicrogame):
    instruction = "Controller: Stick/D-Pad laufen, A/X springen | Tastatur: A/D/Pfeile + Leertaste"

    JUMP_BUFFER_TIME = 0.14
    COYOTE_TIME = 0.10

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player_pos = pygame.Vector2(90, 635)
        self.player_vel = pygame.Vector2(0, 0)
        self.player_size = pygame.Vector2(34, 48)
        self.speed = 280
        self.jump = 600
        self.gravity = 1500
        self.on_ground = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        self.answer_font = ui.font(18, True)

        self.course_platforms, answer_slots = self._generate_platforms()
        self.platforms = self.course_platforms
        self.doors = []
        for choice, slot in answer_slots:
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.answer_font,
                min_width=170,
                max_width=290,
                min_height=72,
                padding_x=18,
                padding_y=12,
                line_gap=1,
            )
            door = pygame.Rect(0, 0, width, height)
            door.midbottom = (slot.centerx, slot.top)
            self.doors.append((choice, door))

    def _generate_platforms(self) -> tuple[list[pygame.Rect], list[tuple[object, pygame.Rect]]]:
        """Build a procedural course whose complete route is always reachable."""
        floor = pygame.Rect(0, 690, SCREEN_W, 30)
        platforms = [floor]

        previous = floor
        center_x = random.randint(185, 235)
        for index in range(3):
            width = random.randint(205, 245)
            rise = random.randint(68, 76)
            y = previous.top - rise

            if index > 0:
                previous_half = previous.width // 2
                new_half = width // 2
                max_center_step = previous_half + new_half + 35
                center_x = previous.centerx + random.randint(125, max(125, max_center_step))

            center_x = max(width // 2 + 20, min(SCREEN_W - width // 2 - 20, center_x))
            platform = pygame.Rect(0, y, width, 24)
            platform.centerx = center_x
            platforms.append(platform)
            previous = platform

        hub_width = random.randint(820, 880)
        hub_y = previous.top - random.randint(64, 72)
        hub = pygame.Rect(0, hub_y, hub_width, 24)
        hub.left = max(260, min(previous.centerx - 120, SCREEN_W - hub_width - 20))
        platforms.append(hub)

        # These invisible slots only position the floating answer boxes.
        base_centers = [430, 760, 1090]
        answer_slots: list[tuple[object, pygame.Rect]] = []
        for choice, base_center in zip(self.choices, base_centers):
            slot = pygame.Rect(0, 0, 1, 1)
            slot.centerx = base_center + random.randint(-8, 8)
            slot.y = hub.top - random.randint(64, 72)
            answer_slots.append((choice, slot))

        return platforms, answer_slots

    def _player_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, int(self.player_size.x), int(self.player_size.y))
        rect.midbottom = (int(self.player_pos.x), int(self.player_pos.y))
        return rect

    def _start_jump(self) -> None:
        self.player_vel.y = -self.jump
        self.on_ground = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

    def update(self, dt: float) -> None:
        self.player_vel.x = self.controls.move_x * self.speed

        if self.controls.pressed("action"):
            self.jump_buffer_timer = self.JUMP_BUFFER_TIME
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        if self.on_ground:
            self.coyote_timer = self.COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if self.jump_buffer_timer > 0.0 and (self.on_ground or self.coyote_timer > 0.0):
            self._start_jump()

        self.player_pos.x += self.player_vel.x * dt

        old_bottom = self._player_rect().bottom
        self.player_vel.y += self.gravity * dt
        self.player_pos.y += self.player_vel.y * dt
        rect = self._player_rect()
        self.on_ground = False
        if self.player_vel.y >= 0:
            for platform in self.platforms:
                if rect.colliderect(platform) and old_bottom <= platform.top + 8:
                    rect.bottom = platform.top
                    self.player_pos.y = rect.bottom
                    self.player_vel.y = 0
                    self.on_ground = True
                    break

        if self.on_ground and self.jump_buffer_timer > 0.0:
            self._start_jump()

        self.player_pos.x = max(18, min(SCREEN_W - 18, self.player_pos.x))
        if self.player_pos.y > SCREEN_H + 100:
            self.player_pos.update(90, 635)
            self.player_vel.update(0, 0)
            self.on_ground = False
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0

        p_rect = self._player_rect()
        for choice, door in self.doors:
            if p_rect.colliderect(door):
                self.choose(choice)
                break

    def draw(self) -> None:
        self.screen.fill((16, 21, 36))
        self.draw_common()
        pygame.draw.rect(self.screen, (25, 32, 55), pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP))

        for platform in self.platforms:
            pygame.draw.rect(self.screen, (71, 86, 112), platform, border_radius=7)
            pygame.draw.rect(
                self.screen,
                ui.ACCENT,
                pygame.Rect(platform.x, platform.y, platform.width, 5),
                border_radius=4,
            )

        for choice, door in self.doors:
            pygame.draw.rect(self.screen, (44, 55, 86), door, border_radius=12)
            pygame.draw.rect(self.screen, ui.GOLD, door, 3, border_radius=12)
            ui.draw_wrapped(
                self.screen,
                choice.text,
                self.answer_font,
                ui.TEXT,
                door.inflate(-24, -18),
                center=True,
                line_gap=1,
                vertical_center=True,
            )

        p = self._player_rect()
        pygame.draw.rect(self.screen, ui.ACCENT_2, p, border_radius=8)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx - 7, p.y + 14), 3)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx + 7, p.y + 14), 3)
