from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from .. import ui
from ..input import Controls

SCREEN_W = 1280
SCREEN_H = 720
PLAY_TOP = 190


@dataclass
class AnswerChoice:
    text: str
    original_index: int


class BaseMicrogame:
    instruction = ""

    def __init__(
        self,
        screen: pygame.Surface,
        question: dict,
        score: int,
        mastery: int,
        controls: Controls,
    ) -> None:
        self.screen = screen
        self.question = question
        self.score = score
        self.mastery = mastery
        self.controls = controls
        self.done = False
        self.correct = False
        self.choices = [AnswerChoice(text, index) for index, text in enumerate(question["answers"])]
        random.shuffle(self.choices)

    def choose(self, choice: AnswerChoice) -> None:
        self.done = True
        self.correct = choice.original_index == self.question["correct"]

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw_common(self) -> None:
        ui.draw_question_header(self.screen, self.question, self.score, self.mastery)
        fnt = ui.font(19, True)
        hint = fnt.render(self.instruction, True, ui.MUTED)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 180)))

    def draw(self) -> None:
        raise NotImplementedError
