from __future__ import annotations

import random

import pygame

from . import ui
from .data import QUESTIONS
from .input import Controls
from .microgames import MICROGAME_TYPES, SCREEN_H, SCREEN_W
from .progress import MASTERY_TARGET, ProgressStore


class ToxiGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Toxi - Toxicology Microgames")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.controls = Controls()
        self.question_by_id = {q["id"]: q for q in QUESTIONS}
        self.progress = ProgressStore(list(self.question_by_id))
        self.state = "menu"
        self.current_question: dict | None = None
        self.current_microgame = None
        self.last_correct = False
        self.last_became_learned = False
        self.last_mastery_before = 0

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

            # Polling after pygame.event.get() keeps keyboard and SDL controller
            # state current and gives us edge-triggered A/B/X/Y actions.
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
        if self.current_microgame.done:
            question_id = self.current_question["id"]
            self.last_mastery_before = self.progress.points(question_id)
            self.last_correct = self.current_microgame.correct
            self.progress.record_result(question_id, self.last_correct)
            now = self.progress.points(question_id)
            self.last_became_learned = self.last_mastery_before < MASTERY_TARGET and now >= MASTERY_TARGET
            if self.last_correct:
                self.controls.rumble(0.15, 0.55, 160)
            else:
                self.controls.rumble(0.5, 0.15, 240)
            self.state = "result"
            self.controls.consume_presses()

    def _start_next_round(self) -> None:
        pending = self.progress.pending_ids()
        if not pending:
            self.state = "finished"
            self.current_question = None
            self.current_microgame = None
            self.controls.consume_presses()
            return

        min_points = min(self.progress.points(qid) for qid in pending)
        pool = [qid for qid in pending if self.progress.points(qid) <= min_points + 1]
        qid = random.choice(pool)
        question = self.question_by_id[qid]

        # Attempts alternate a question's two levels so both variants are used.
        attempt = self.progress.attempts(qid)
        variant_name = question["variants"][attempt % len(question["variants"])]
        microgame_cls = MICROGAME_TYPES[variant_name]

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
        subtitle = ui.font(28, True).render("Toxikologie lernen als 2D-Microgame-Mix", True, ui.TEXT)
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

        start = ui.font(28, True).render("A / START - starten", True, ui.ACCENT_2)
        self.screen.blit(start, start.get_rect(center=(SCREEN_W // 2, 565)))
        controller_help = ui.font(21, True).render("Y - Fortschritt zurücksetzen   |   B - beenden", True, ui.TEXT)
        self.screen.blit(controller_help, controller_help.get_rect(center=(SCREEN_W // 2, 610)))
        keyboard = ui.font(17).render("Tastatur-Fallback: ENTER/LEERTASTE starten, R reset, ESC zurück", True, ui.MUTED)
        self.screen.blit(keyboard, keyboard.get_rect(center=(SCREEN_W // 2, 650)))

    def _draw_result(self) -> None:
        self.screen.fill(ui.BG)
        question = self.current_question
        if not question:
            return
        color = ui.ACCENT if self.last_correct else ui.DANGER
        heading_text = "RICHTIG! +1" if self.last_correct else "NOCH NICHT"
        heading = ui.font(60, True).render(heading_text, True, color)
        self.screen.blit(heading, heading.get_rect(center=(SCREEN_W // 2, 90)))

        panel = pygame.Rect(150, 150, 980, 430)
        ui.draw_panel(self.screen, panel)
        q_font = ui.font(29, True)
        ui.draw_wrapped(self.screen, question["question"], q_font, ui.TEXT, pygame.Rect(200, 185, 880, 80), center=True)

        correct_text = question["answers"][question["correct"]]
        ans_font = ui.font(27, True)
        ui.draw_wrapped(self.screen, f"Richtige Antwort: {correct_text}", ans_font, ui.ACCENT, pygame.Rect(220, 285, 840, 75), center=True)

        expl_font = ui.font(23)
        ui.draw_wrapped(self.screen, question["explanation"], expl_font, ui.TEXT, pygame.Rect(225, 370, 830, 110), center=True)

        mastery = self.progress.points(question["id"])
        status = f"Lernfortschritt: {mastery}/{MASTERY_TARGET} | Quelle in den Notizen: Seite {question['page']}"
        status_img = ui.font(21, True).render(status, True, ui.GOLD)
        self.screen.blit(status_img, status_img.get_rect(center=(SCREEN_W // 2, 525)))
        if self.last_became_learned:
            learned = ui.font(24, True).render("GELERNT - diese Frage wird nicht mehr gezogen!", True, ui.ACCENT)
            self.screen.blit(learned, learned.get_rect(center=(SCREEN_W // 2, 565)))

        prompt = ui.font(25, True).render("A - nächstes Microgame   |   B - Menü", True, ui.ACCENT_2)
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_W // 2, 635)))
        keyboard = ui.font(17).render("Tastatur: ENTER/LEERTASTE = weiter, ESC = Menü", True, ui.MUTED)
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
