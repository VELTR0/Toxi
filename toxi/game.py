from __future__ import annotations

import random

import pygame

from . import ui
from .data import QUESTIONS
from .input import Controls
from .microgames import MICROGAME_TYPES, SCREEN_H, SCREEN_W
from .progress import MASTERY_TARGET, ProgressStore


class ToxiGame:
    def __init__(
        self,
        *,
        debug_microgame: str | None = None,
        debug_question_id: str | None = None,
    ) -> None:
        pygame.init()
        pygame.display.set_caption("Toxi - Toxicology Microgames")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.controls = Controls()
        self.question_by_id = {q["id"]: q for q in QUESTIONS}
        self.progress = ProgressStore(list(self.question_by_id))

        if debug_microgame is not None and debug_microgame not in MICROGAME_TYPES:
            raise ValueError(f"Unbekanntes Microgame: {debug_microgame}")
        if debug_question_id is not None and debug_question_id not in self.question_by_id:
            raise ValueError(f"Unbekannte Frage-ID: {debug_question_id}")
        if debug_question_id is not None and debug_microgame is None:
            raise ValueError("--debug-question benötigt --debug-microgame")

        self.debug_microgame = debug_microgame
        self.debug_question_id = debug_question_id

        self.state = "menu"
        self.current_question: dict | None = None
        self.current_microgame = None
        self.last_correct = False
        self.last_became_learned = False
        self.last_mastery_before = 0

        if self.debug_microgame:
            self._start_debug_round()

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                if self.state == "microgame" and self.current_microgame:
                    self.current_microgame.handle_event(event)

            self.controls.update()
            self._handle_controls()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_controls(self) -> None:
        if self.state == "menu":
            if self.controls.pressed("confirm"):
                self._start_next_round()
            elif self.controls.pressed("reset"):
                self.progress.reset()
                self.controls.rumble(0.2, 0.35, 120)
            elif self.controls.pressed("back"):
                self.running = False

        elif self.state == "microgame":
            if self.controls.pressed("back"):
                self.state = "menu"
                self.current_microgame = None
                self.current_question = None
                self.controls.consume_presses()

        elif self.state == "result":
            if self.controls.pressed("confirm"):
                self._start_next_round()
            elif self.controls.pressed("back"):
                self.state = "menu"
                self.current_microgame = None
                self.controls.consume_presses()

        elif self.state == "finished":
            if self.controls.pressed("reset"):
                self.progress.reset()
                self.state = "menu"
                self.controls.rumble(0.2, 0.45, 180)
                self.controls.consume_presses()
            elif self.controls.pressed("back"):
                self.running = False

    def _update(self, dt: float) -> None:
        if self.state != "microgame" or not self.current_microgame:
            return
        self.current_microgame.update(dt)
        if not self.current_microgame.done:
            return

        question_id = self.current_question["id"]
        self.last_mastery_before = self.progress.points(question_id)
        self.last_correct = self.current_microgame.correct
        self.last_became_learned = False

        # Debug runs are deliberately read-only: testing a specific microgame
        # must not change score, attempts or learning progress.
        if not self.debug_microgame:
            self.progress.record_result(question_id, self.last_correct)
            now = self.progress.points(question_id)
            self.last_became_learned = self.last_mastery_before < MASTERY_TARGET and now >= MASTERY_TARGET

        if self.last_correct:
            self.controls.rumble(0.15, 0.55, 160)
        else:
            self.controls.rumble(0.5, 0.15, 240)
        self.state = "result"
        self.controls.consume_presses()

    def _instantiate_microgame(self, question: dict, variant_name: str) -> None:
        microgame_cls = MICROGAME_TYPES[variant_name]
        qid = question["id"]
        self.current_question = question
        self.current_microgame = microgame_cls(
            self.screen,
            question,
            self.progress.global_score,
            self.progress.points(qid),
            self.controls,
        )
        self.state = "microgame"
        self.controls.consume_presses()

    def _start_debug_round(self) -> None:
        if not self.debug_microgame:
            return
        if self.debug_question_id:
            question = self.question_by_id[self.debug_question_id]
        else:
            question = random.choice(QUESTIONS)
        self._instantiate_microgame(question, self.debug_microgame)

    def _start_next_round(self) -> None:
        if self.debug_microgame:
            self._start_debug_round()
            return

        pending = self.progress.pending_ids()
        if not pending:
            self.state = "finished"
            self.current_question = None
            self.current_microgame = None
            self.controls.consume_presses()
            return

        min_points = min(self.progress.points(qid) for qid in pending)
        pool = [qid for qid in pending if self.progress.points(qid) <= min_points + 1]

        # Each question still alternates its assigned variants by attempt, but
        # the scheduler first groups the currently eligible questions by their
        # NEXT microgame and chooses a group uniformly. This prevents a game
        # type with many question assignments from dominating the rotation.
        variant_buckets: dict[str, list[str]] = {}
        for qid in pool:
            question = self.question_by_id[qid]
            attempt = self.progress.attempts(qid)
            variant_name = question["variants"][attempt % len(question["variants"])]
            variant_buckets.setdefault(variant_name, []).append(qid)

        variant_name = random.choice(list(variant_buckets))
        qid = random.choice(variant_buckets[variant_name])
        question = self.question_by_id[qid]
        self._instantiate_microgame(question, variant_name)

    def _draw(self) -> None:
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "microgame" and self.current_microgame:
            self.current_microgame.draw()
        elif self.state == "result":
            self._draw_result()
        elif self.state == "finished":
            self._draw_finished()

    def _draw_controller_status(self, y: int) -> None:
        label = f"Controller: {self.controls.controller_name}"
        color = ui.ACCENT if self.controls.connected else ui.MUTED
        img = ui.font(18, True).render(label, True, color)
        self.screen.blit(img, img.get_rect(center=(SCREEN_W // 2, y)))

    def _draw_menu(self) -> None:
        self.screen.fill(ui.BG)
        title = ui.font(78, True).render("TOXI", True, ui.ACCENT)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 105)))
        subtitle = ui.font(28, True).render("Toxikologie spielerisch lernen", True, ui.TEXT)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 165)))
        self._draw_controller_status(205)

        learned = self.progress.learned_count()
        total = len(QUESTIONS)
        panel = pygame.Rect(250, 235, 780, 285)
        ui.draw_panel(self.screen, panel)
        big = ui.font(34, True)
        normal = ui.font(24)
        self.screen.blit(big.render(f"Global Score: {self.progress.global_score}", True, ui.GOLD), (300, 275))
        self.screen.blit(big.render(f"Gelernt: {learned}/{total} Fragen", True, ui.ACCENT), (300, 325))
        ui.draw_wrapped(
            self.screen,
            "Jede Frage hat zwei abwechselnde Microgame-Level. Ein Sieg gibt der Frage +1 Lernpunkt. Bei 3/3 erscheint sie nicht mehr.",
            normal,
            ui.TEXT,
            pygame.Rect(300, 385, 680, 100),
            center=True,
        )

        controller_help = ui.font(21, True).render("Controller: A / START - starten   |   Y - Reset Progress   |   B - beenden", True, ui.TEXT)
        self.screen.blit(controller_help, controller_help.get_rect(center=(SCREEN_W // 2, 610)))
        keyboard = ui.font(17).render("Tastatur: ENTER/LEERTASTE starten, R Reset Progress, ESC beenden", True, ui.MUTED)
        self.screen.blit(keyboard, keyboard.get_rect(center=(SCREEN_W // 2, 650)))

    def _draw_result(self) -> None:
        self.screen.fill(ui.BG)
        question = self.current_question
        if not question:
            return
        color = ui.ACCENT if self.last_correct else ui.DANGER
        heading_text = "RICHTIG! +1" if self.last_correct else "FALSCH"
        if self.debug_microgame:
            heading_text = "DEBUG: RICHTIG" if self.last_correct else "DEBUG: FALSCH"
        heading = ui.font(60, True).render(heading_text, True, color)
        self.screen.blit(heading, heading.get_rect(center=(SCREEN_W // 2, 90)))

        panel = pygame.Rect(150, 150, 980, 430)
        ui.draw_panel(self.screen, panel)

        # After every microgame, only the explanation is repeated here.
        expl_font = ui.font(25)
        ui.draw_wrapped(
            self.screen,
            question["explanation"],
            expl_font,
            ui.TEXT,
            pygame.Rect(225, 215, 830, 245),
            center=True,
            vertical_center=True,
            line_gap=5,
        )

        mastery = self.progress.points(question["id"])
        status = f"Lernfortschritt: {mastery}/{MASTERY_TARGET} | Quelle in den Notizen: Seite {question['page']}"
        if self.debug_microgame:
            status += " | DEBUG: Fortschritt unverändert"
        status_img = ui.font(21, True).render(status, True, ui.GOLD)
        self.screen.blit(status_img, status_img.get_rect(center=(SCREEN_W // 2, 525)))
        if self.last_became_learned:
            learned = ui.font(24, True).render("GELERNT - diese Frage wird nicht mehr gezogen!", True, ui.ACCENT)
            self.screen.blit(learned, learned.get_rect(center=(SCREEN_W // 2, 565)))

        prompt_text = "A - Debug erneut starten   |   B - Menü" if self.debug_microgame else ""
        prompt = ui.font(25, True).render(prompt_text, True, ui.ACCENT_2)
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_W // 2, 635)))
        keyboard = ui.font(17).render("", True, ui.MUTED)
        self.screen.blit(keyboard, keyboard.get_rect(center=(SCREEN_W // 2, 675)))

    def _draw_finished(self) -> None:
        self.screen.fill((12, 24, 28))
        title = ui.font(66, True).render("TOXI ABGESCHLOSSEN", True, ui.ACCENT)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 135)))
        trophy = ui.font(105, True).render("★", True, ui.GOLD)
        self.screen.blit(trophy, trophy.get_rect(center=(SCREEN_W // 2, 260)))
        score = ui.font(40, True).render(f"Finaler Global Score: {self.progress.global_score}", True, ui.TEXT)
        self.screen.blit(score, score.get_rect(center=(SCREEN_W // 2, 380)))
        detail = ui.font(28).render(f"Alle {len(QUESTIONS)} Fragen sind bei 3/3 Lernpunkten.", True, ui.TEXT)
        self.screen.blit(detail, detail.get_rect(center=(SCREEN_W // 2, 435)))
        reset = ui.font(25, True).render("Y - komplett neu starten   |   B - beenden", True, ui.ACCENT_2)
        self.screen.blit(reset, reset.get_rect(center=(SCREEN_W // 2, 545)))
        keyboard = ui.font(17).render("Tastatur: R = neu starten, ESC = beenden", True, ui.MUTED)
        self.screen.blit(keyboard, keyboard.get_rect(center=(SCREEN_W // 2, 590)))
        self._draw_controller_status(640)
