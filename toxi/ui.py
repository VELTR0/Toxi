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


def wrap_text(text: str, fnt: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if fnt.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


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
    """Return a box size that grows with the answer text.

    Short answers stay compact. Long answers grow horizontally up to max_width
    and then vertically according to the wrapped line count, so text never has
    to spill outside a fixed-size answer object.
    """
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
        # A centered square around 1.4r wide/high sits comfortably inside a
        # circle while leaving visible breathing room around the text.
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


def draw_question_header(surface: pygame.Surface, question: dict, score: int, mastery: int) -> None:
    panel = pygame.Rect(30, 24, surface.get_width() - 60, 150)
    draw_panel(surface, panel)
    small = font(20, True)
    body = font(28, True)
    surface.blit(small.render(f"Score {score}", True, GOLD), (50, 42))
    mastery_text = "Fortschritt: " + "●" * mastery + "○" * (3 - mastery)
    mastery_img = small.render(mastery_text, True, ACCENT)
    surface.blit(mastery_img, (panel.right - mastery_img.get_width() - 20, 42))
    draw_wrapped(surface, question["question"], body, TEXT, pygame.Rect(50, 80, panel.width - 40, 80), center=True)


def draw_button(surface: pygame.Surface, rect: pygame.Rect, text: str, hovered: bool = False) -> None:
    color = PANEL_2 if not hovered else (53, 66, 91)
    pygame.draw.rect(surface, color, rect, border_radius=14)
    pygame.draw.rect(surface, ACCENT_2, rect, 2, border_radius=14)
    fnt = font(25, True)
    label = fnt.render(text, True, TEXT)
    surface.blit(label, label.get_rect(center=rect.center))
