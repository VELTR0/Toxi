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

        self.course_platforms, self.answer_platforms = self._generate_platforms()
        self.platforms = self.course_platforms + [platform for _, platform in self.answer_platforms]
        self.doors = []
        for choice, platform in self.answer_platforms:
            door = pygame.Rect(0, 0, platform.width - 18, 72)
            door.midbottom = (platform.centerx, platform.top)
            self.doors.append((choice, door))

    def _generate_platforms(self) -> tuple[list[pygame.Rect], list[tuple[object, pygame.Rect]]]:
        """Build a fresh but deliberately reachable one-screen course.

        The lower staircase is randomized each round. A wide final staging
        platform gives the player room to choose before jumping to one of three
        physically separate answer platforms.
        """
        platforms = [pygame.Rect(0, 690, SCREEN_W, 30)]

        # Procedural staircase. Vertical and horizontal gaps stay inside the
        # character's jump envelope so random layouts cannot become impossible.
        center_x = random.randint(185, 225)
        y_bases = (590, 520, 450)
        for index, base_y in enumerate(y_bases):
            width = random.randint(190, 235)
            y = base_y + random.randint(-10, 10)
            if index > 0:
                center_x += random.randint(155, 205)
            center_x = max(width // 2 + 20, min(SCREEN_W - width // 2 - 20, center_x))
            platform = pygame.Rect(0, y, width, 24)
            platform.centerx = center_x
            platforms.append(platform)

        # Last neutral platform: wide enough to stand below any answer and
        # deliberately separated from the answer row above it.
        hub_y = random.randint(375, 392)
        hub_width = random.randint(790, 850)
        hub = pygame.Rect(0, hub_y, hub_width, 24)
        hub.x = random.randint(340, 380)
        if hub.right > SCREEN_W - 20:
            hub.right = SCREEN_W - 20
        platforms.append(hub)

        # Each answer gets its own platform. Their exact position and height
        # vary slightly, but all three remain reachable directly from the hub.
        answer_width = 210
        base_centers = [470, 750, 1030]
        answer_platforms: list[tuple[object, pygame.Rect]] = []
        for choice, base_center in zip(self.choices, base_centers):
            platform = pygame.Rect(0, 0, answer_width, 22)
            platform.centerx = base_center + random.randint(-18, 18)
            platform.y = hub_y - random.randint(88, 102)
            answer_platforms.append((choice, platform))

        return platforms, answer_platforms

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

        # Jump buffering makes rapid presses reliable: a jump pressed shortly
        # before landing is remembered and fires as soon as the player lands.
        if self.controls.pressed("action"):
            self.jump_buffer_timer = self.JUMP_BUFFER_TIME
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        # A tiny coyote-time window also prevents jumps from being lost on the
        # exact frame the player walks off a platform edge.
        if self.on_ground:
            self.coyote_timer = self.COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if self.jump_buffer_timer > 0.0 and (self.on_ground or self.coyote_timer > 0.0):
            self._start_jump()

        self.player_pos.x += self.player_vel.x * dt
        rect = self._player_rect()
        for platform in self.platforms:
            if rect.colliderect(platform):
                if self.player_vel.x > 0:
                    rect.right = platform.left
                elif self.player_vel.x < 0:
                    rect.left = platform.right
                self.player_pos.x = rect.centerx

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

        # If jump was pressed just before touching down, launch immediately
        # instead of requiring another button press after the landing frame.
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

        answer_rects = {id(platform) for _, platform in self.answer_platforms}
        for platform in self.platforms:
            is_answer = id(platform) in answer_rects
            body_color = (58, 70, 101) if is_answer else (71, 86, 112)
            edge_color = ui.GOLD if is_answer else ui.ACCENT
            pygame.draw.rect(self.screen, body_color, platform, border_radius=7)
            pygame.draw.rect(
                self.screen,
                edge_color,
                pygame.Rect(platform.x, platform.y, platform.width, 5),
                border_radius=4,
            )

        answer_font = ui.font(18, True)
        for choice, door in self.doors:
            pygame.draw.rect(self.screen, (44, 55, 86), door, border_radius=12)
            pygame.draw.rect(self.screen, ui.GOLD, door, 3, border_radius=12)
            ui.draw_wrapped(self.screen, choice.text, answer_font, ui.TEXT, door.inflate(-12, -10), center=True, line_gap=1)

        p = self._player_rect()
        pygame.draw.rect(self.screen, ui.ACCENT_2, p, border_radius=8)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx - 7, p.y + 14), 3)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx + 7, p.y + 14), 3)
