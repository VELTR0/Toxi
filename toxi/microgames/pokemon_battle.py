from __future__ import annotations

import math

import pygame

from .. import ui
from .base import BaseMicrogame, PLAY_TOP, SCREEN_H, SCREEN_W


class PokemonBattle(BaseMicrogame):
    """A controller-friendly retro creature-battle style question duel.

    The visuals are original procedural shapes, but the flow deliberately evokes
    a classic handheld monster battle: the player chooses one of three attacks,
    lunges forward, and either defeats the question or gets counter-attacked.
    """

    PLAYER_ATTACK_TIME = 0.36
    ENEMY_ATTACK_TIME = 0.36
    DEFEAT_TIME = 1.05
    GROUND_Y = 455

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.selected = 0
        self.phase = "select"
        self.phase_timer = 0.0
        self.chosen = None
        self.chosen_correct = False

        self.player_base = pygame.Vector2(285, 400)
        self.enemy_base = pygame.Vector2(995, 300)

        self.attack_font = ui.font(18, True)
        self.attack_rects: list[pygame.Rect] = []
        centers = [220, 640, 1060]
        for choice, center_x in zip(self.choices, centers):
            width, height = ui.adaptive_answer_size(
                choice.text,
                self.attack_font,
                min_width=220,
                max_width=350,
                min_height=72,
                padding_x=18,
                padding_y=12,
                line_gap=2,
            )
            rect = pygame.Rect(0, 0, width, height)
            rect.midbottom = (center_x, 695)
            self.attack_rects.append(rect)

    def _start_attack(self) -> None:
        if self.phase != "select" or self.done:
            return
        self.chosen = self.choices[self.selected]
        self.chosen_correct = self.chosen.original_index == self.question["correct"]
        self.phase = "player_attack"
        self.phase_timer = self.PLAYER_ATTACK_TIME

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.phase != "select" or self.done:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.attack_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    self._start_attack()
                    break

    def update(self, dt: float) -> None:
        if self.phase == "select":
            if self.controls.pressed("left") or self.controls.pressed("up"):
                self.selected = (self.selected - 1) % len(self.choices)
            elif self.controls.pressed("right") or self.controls.pressed("down"):
                self.selected = (self.selected + 1) % len(self.choices)

            if self.controls.pressed("confirm") or self.controls.pressed("action"):
                self._start_attack()
            return

        self.phase_timer = max(0.0, self.phase_timer - dt)
        if self.phase_timer > 0.0:
            return

        if self.phase == "player_attack":
            if self.chosen_correct:
                self.phase = "enemy_defeat"
                self.phase_timer = self.DEFEAT_TIME
            else:
                self.phase = "enemy_attack"
                self.phase_timer = self.ENEMY_ATTACK_TIME
        elif self.phase == "enemy_attack":
            self.phase = "player_defeat"
            self.phase_timer = self.DEFEAT_TIME
        elif self.phase == "enemy_defeat":
            self.correct = True
            self.done = True
        elif self.phase == "player_defeat":
            self.correct = False
            self.done = True

    @staticmethod
    def _lunge_offset(timer: float, duration: float, direction: float) -> float:
        progress = 1.0 - timer / duration
        return math.sin(progress * math.pi) * 82.0 * direction

    @staticmethod
    def _defeat_offset(timer: float, duration: float) -> tuple[float, float]:
        progress = 1.0 - timer / duration
        shake = math.sin(progress * math.pi * 12.0) * (12.0 * (1.0 - progress))
        sink = 165.0 * progress * progress
        return shake, sink

    def _player_position(self) -> pygame.Vector2:
        pos = self.player_base.copy()
        if self.phase == "player_attack":
            pos.x += self._lunge_offset(self.phase_timer, self.PLAYER_ATTACK_TIME, 1.0)
        elif self.phase == "player_defeat":
            shake, sink = self._defeat_offset(self.phase_timer, self.DEFEAT_TIME)
            pos.x += shake
            pos.y += sink
        return pos

    def _enemy_position(self) -> pygame.Vector2:
        pos = self.enemy_base.copy()
        if self.phase == "enemy_attack":
            pos.x += self._lunge_offset(self.phase_timer, self.ENEMY_ATTACK_TIME, -1.0)
        elif self.phase == "enemy_defeat":
            shake, sink = self._defeat_offset(self.phase_timer, self.DEFEAT_TIME)
            pos.x += shake
            pos.y += sink
        return pos

    def _draw_player(self, pos: pygame.Vector2) -> None:
        x, y = int(pos.x), int(pos.y)
        pygame.draw.ellipse(self.screen, (38, 50, 66), pygame.Rect(x - 92, y + 45, 184, 34))
        pygame.draw.circle(self.screen, ui.ACCENT_2, (x, y), 56)
        pygame.draw.circle(self.screen, ui.TEXT, (x, y), 56, 4)
        pygame.draw.circle(self.screen, ui.TEXT, (x - 17, y - 8), 6)
        pygame.draw.circle(self.screen, ui.TEXT, (x + 17, y - 8), 6)
        pygame.draw.arc(self.screen, ui.TEXT, pygame.Rect(x - 22, y - 4, 44, 34), 0.1, math.pi - 0.1, 4)
        badge = ui.font(18, True).render("TOXI", True, ui.GOLD)
        self.screen.blit(badge, badge.get_rect(center=(x, y + 27)))

    def _draw_enemy(self, pos: pygame.Vector2) -> None:
        x, y = int(pos.x), int(pos.y)
        pygame.draw.ellipse(self.screen, (38, 50, 66), pygame.Rect(x - 105, y + 50, 210, 36))
        pygame.draw.circle(self.screen, (73, 61, 102), (x, y), 64)
        pygame.draw.circle(self.screen, ui.GOLD, (x, y), 64, 4)
        question = ui.font(58, True).render("?", True, ui.TEXT)
        self.screen.blit(question, question.get_rect(center=(x, y - 5)))
        label = ui.font(18, True).render("FRAGE", True, ui.GOLD)
        self.screen.blit(label, label.get_rect(center=(x, y + 42)))

    def _draw_status_panel(self) -> None:
        panel = pygame.Rect(410, 220, 455, 95)
        ui.draw_panel(self.screen, panel, color=(32, 39, 56), radius=14)
        if self.phase == "select":
            text = "Welche Attacke setzt du ein?"
        elif self.phase == "player_attack":
            text = f"TOXI setzt {self.chosen.text} ein!"
        elif self.phase == "enemy_defeat":
            text = "Volltreffer! Die Frage wurde besiegt."
        elif self.phase == "enemy_attack":
            text = "Nicht effektiv... Die Frage greift an!"
        else:
            text = "TOXI wurde getroffen."
        ui.draw_wrapped(
            self.screen,
            text,
            ui.font(21, True),
            ui.TEXT,
            panel.inflate(-24, -18),
            center=True,
            vertical_center=True,
            line_gap=2,
        )

    def draw(self) -> None:
        self.screen.fill((18, 27, 42))
        self.draw_common()

        arena = pygame.Rect(0, PLAY_TOP, SCREEN_W, SCREEN_H - PLAY_TOP)
        pygame.draw.rect(self.screen, (34, 52, 66), arena)
        pygame.draw.rect(self.screen, (51, 76, 72), pygame.Rect(0, self.GROUND_Y, SCREEN_W, SCREEN_H - self.GROUND_Y))
        for x in range(0, SCREEN_W, 80):
            pygame.draw.line(self.screen, (56, 83, 78), (x, self.GROUND_Y), (x + 140, SCREEN_H), 2)

        # Clip the combatants at the ground line. During defeat they shake and
        # move downward, so the ground progressively hides them instead of the
        # sprite simply sliding across the foreground.
        old_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, PLAY_TOP, SCREEN_W, self.GROUND_Y - PLAY_TOP))
        self._draw_player(self._player_position())
        self._draw_enemy(self._enemy_position())
        self.screen.set_clip(old_clip)

        self._draw_status_panel()

        for index, (choice, rect) in enumerate(zip(self.choices, self.attack_rects)):
            selected = index == self.selected
            fill = (55, 68, 94) if selected else (42, 50, 69)
            border = ui.GOLD if selected else ui.ACCENT_2
            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(self.screen, border, rect, 4 if selected else 2, border_radius=14)
            ui.draw_wrapped(
                self.screen,
                choice.text,
                self.attack_font,
                ui.TEXT,
                rect.inflate(-18, -10),
                center=True,
                vertical_center=True,
                line_gap=2,
            )
