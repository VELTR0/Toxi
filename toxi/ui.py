from __future__ import annotations

import pygame


BG = (17, 20, 30)
PANEL = (28, 34, 49)
PANEL_2 = (38, 45, 63)
TEXT = (242, 245, 250)
MUTED = (168, 178, 198)
ACCENT = (89, 214, 170)
ACCENT_2 = (108, 170, 255)
DANGER = (255, 104, 112)
GOLD = (255, 211, 92)


def font(size: int, bold: bool = False) -> pygame.font.Font:
    names = ["segoeui", "arial", "dejavusans"]
    for name in names:
        found = pygame.font.match_font(name, bold=bold)
        if found:
            return pygame.font.Font(found, size)
    return pygame.font.Font(None, size)


def _split_long_word(word: str, fnt: pygame.font.Font, max_width: int) -> list[str]:
    """Split a single oversized token so it can never escape its container."""
    if fnt.size(word)[0] <= max_width:
        return [word]

    parts: list[str] = []
    remaining = word
    while remaining:
        if fnt.size(remaining)[0] <= max_width:
            parts.append(remaining)
            break

        cut = 1
        last_hyphen = -1
        for index in range(1, len(remaining) + 1):
            if fnt.size(remaining[:index])[0] > max_width:
                break
            cut = index
            if remaining[index - 1] == "-":
                last_hyphen = index

        if last_hyphen > 0:
            cut = last_hyphen
        parts.append(remaining[:cut])
        remaining = remaining[cut:]

    return parts


def wrap_text(text: str, fnt: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    max_width = max(1, max_width)
    lines: list[str] = []
    current = ""

    for word in words:
        parts = _split_long_word(word, fnt, max_width)
        for part_index, part in enumerate(parts):
            candidate = part if not current else f"{current} {part}"
            if fnt.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = part

            # A split token must continue on the next line. Prefer explicit
            # hyphen boundaries when available, otherwise fall back to a safe
            # character split rather than letting text protrude from the shape.
            if part_index < len(parts) - 1:
                lines.append(current)
                current = ""

    if current:
        lines.append(current)
    return lines or [""]


def measure_wrapped(
    text: str,
    fnt: pygame.font.Font,
    max_width: int,
    *,
    line_gap: int = 5,
) -> tuple[int, int, list[str]]:
    lines = wrap_text(text, fnt, max(1, max_width))
    widths = [fnt.size(line)[0] for line in lines]
    line_height = fnt.get_height()
    height = len(lines) * line_height + max(0, len(lines) - 1) * line_gap
    return max(widths, default=0), height, lines


def adaptive_answer_size(
    text: str,
    fnt: pygame.font.Font,
    *,
    min_width: int = 140,
    max_width: int = 300,
    min_height: int = 64,
    padding_x: int = 18,
    padding_y: int = 12,
    line_gap: int = 2,
) -> tuple[int, int]:
    """Return a box size that grows with the answer text."""
    natural_width = fnt.size(text)[0] + padding_x * 2
    width = max(min_width, min(max_width, natural_width))
    _, content_height, _ = measure_wrapped(
        text,
        fnt,
        width - padding_x * 2,
        line_gap=line_gap,
    )
    height = max(min_height, content_height + padding_y * 2)
    return int(width), int(height)


def adaptive_circle_radius(
    text: str,
    fnt: pygame.font.Font,
    *,
    min_radius: int = 64,
    max_radius: int = 130,
    padding: int = 12,
    line_gap: int = 2,
) -> int:
    """Find the smallest circle that comfortably contains wrapped answer text."""
    for radius in range(min_radius, max_radius + 1, 3):
        inner = max(40, int(radius * 1.4) - padding * 2)
        content_width, content_height, _ = measure_wrapped(
            text,
            fnt,
            inner,
            line_gap=line_gap,
        )
        if content_width <= inner and content_height <= inner:
            return radius
    return max_radius


def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    fnt: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    *,
    center: bool = False,
    line_gap: int = 5,
    vertical_center: bool = False,
) -> int:
    lines = wrap_text(text, fnt, rect.width)
    line_height = fnt.get_height()
    total_height = len(lines) * line_height + max(0, len(lines) - 1) * line_gap
    y = rect.centery - total_height // 2 if vertical_center else rect.y
    for line in lines:
        rendered = fnt.render(line, True, color)
        x = rect.centerx - rendered.get_width() // 2 if center else rect.x
        surface.blit(rendered, (x, y))
        y += line_height + line_gap
    return y


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, color=PANEL, radius: int = 18) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_question_header(
    surface: pygame.Surface,
    question: dict,
    score: int,
    mastery: int,
    task_prompt: str = "Wähle die richtige Antwort!",
) -> None:
    """Draw the shared question header and an optional compact task field below it."""
    panel = pygame.Rect(30, 24, surface.get_width() - 60, 150)
    draw_panel(surface, panel)
    small = font(20, True)
    surface.blit(small.render(f"Score {score}", True, GOLD), (50, 38))
    mastery_text = "Fortschritt: " + "●" * mastery + "○" * (3 - mastery)
    mastery_img = small.render(mastery_text, True, ACCENT)
    surface.blit(mastery_img, (panel.right - mastery_img.get_width() - 20, 38))

    question_rect = pygame.Rect(50, 65, panel.width - 40, 70)
    body = font(28, True)
    for size in (28, 26, 24, 22):
        candidate = font(size, True)
        _, text_height, _ = measure_wrapped(question["question"], candidate, question_rect.width, line_gap=3)
        body = candidate
        if text_height <= question_rect.height:
            break
    draw_wrapped(
        surface,
        question["question"],
        body,
        TEXT,
        question_rect,
        center=True,
        vertical_center=True,
        line_gap=3,
    )

    # An empty task prompt deliberately disables the task field for that
    # microgame instead of rendering an empty bordered box.
    if not task_prompt.strip():
        return

    prompt_font = font(17, True)
    prompt_width = min(520, max(250, prompt_font.size(task_prompt)[0] + 42))
    prompt = pygame.Rect(0, 0, prompt_width, 30)
    prompt.midbottom = (panel.centerx, panel.bottom - 5)
    pygame.draw.rect(surface, PANEL_2, prompt, border_radius=11)
    pygame.draw.rect(surface, ACCENT_2, prompt, 2, border_radius=11)
    prompt_img = prompt_font.render(task_prompt, True, TEXT)
    surface.blit(prompt_img, prompt_img.get_rect(center=prompt.center))


def draw_button(surface: pygame.Surface, rect: pygame.Rect, text: str, hovered: bool = False) -> None:
    color = PANEL_2 if not hovered else (53, 66, 91)
    pygame.draw.rect(surface, color, rect, border_radius=14)
    pygame.draw.rect(surface, ACCENT_2, rect, 2, border_radius=14)
    fnt = font(25, True)
    label = fnt.render(text, True, TEXT)
    surface.blit(label, label.get_rect(center=rect.center))
