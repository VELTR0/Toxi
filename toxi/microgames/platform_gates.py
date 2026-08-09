from __future__ import annotations

import math
import random
import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W

class PlatformGates(BaseMicrogame):
    instruction = "A/D oder Pfeile: laufen | LEERTASTE: springen | Berühre die richtige Tür"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player_pos = pygame.Vector2(90, 635)
        self.player_vel = pygame.Vector2(0, 0)
        self.player_size = pygame.Vector2(34, 48)
        self.speed = 280
        self.jump = 600
        self.gravity = 1500
        self.on_ground = False
        self.platforms = [
            pygame.Rect(0, 690, SCREEN_W, 30),
            pygame.Rect(180, 580, 230, 24),
            pygame.Rect(450, 490, 230, 24),
            pygame.Rect(720, 400, 230, 24),
            pygame.Rect(900, 320, 380, 24),
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

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.on_ground:
            self.player_vel.y = -self.jump
            self.on_ground = False

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        self.player_vel.x = direction * self.speed

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

        self.player_pos.x = max(18, min(SCREEN_W - 18, self.player_pos.x))
        if self.player_pos.y > SCREEN_H + 100:
            self.player_pos.update(90, 635)
            self.player_vel.update(0, 0)

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
