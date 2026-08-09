from __future__ import annotations

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
        self.platforms = [
            pygame.Rect(0, 690, SCREEN_W, 30),
            pygame.Rect(180, 580, 230, 24),
            pygame.Rect(450, 490, 230, 24),
            pygame.Rect(720, 400, 230, 24),
            pygame.Rect(900, 340, 380, 24),
        ]
        # Nach dem Aufstieg kann man unter allen Türen entlanglaufen und
        # gezielt in die gewünschte Antwort springen.
        door_positions = [
            pygame.Rect(925, 180, 105, 80),
            pygame.Rect(1045, 180, 105, 80),
            pygame.Rect(1165, 180, 105, 80),
        ]
        self.doors = list(zip(self.choices, door_positions))

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
        for platform in self.platforms:
            pygame.draw.rect(self.screen, (71, 86, 112), platform, border_radius=7)
            pygame.draw.rect(self.screen, ui.ACCENT, pygame.Rect(platform.x, platform.y, platform.width, 5), border_radius=4)
        answer_font = ui.font(18, True)
        for choice, door in self.doors:
            pygame.draw.rect(self.screen, (44, 55, 86), door, border_radius=12)
            pygame.draw.rect(self.screen, ui.GOLD, door, 3, border_radius=12)
            ui.draw_wrapped(self.screen, choice.text, answer_font, ui.TEXT, door.inflate(-12, -10), center=True, line_gap=1)
        p = self._player_rect()
        pygame.draw.rect(self.screen, ui.ACCENT_2, p, border_radius=8)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx - 7, p.y + 14), 3)
        pygame.draw.circle(self.screen, ui.TEXT, (p.centerx + 7, p.y + 14), 3)
