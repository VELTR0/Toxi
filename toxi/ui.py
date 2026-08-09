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


def draw_wrapped(
    surface: pygame.Surface,
    text: str,
    fnt: pygame.font.Font,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    *,
    center: bool = False,
    line_gap: int = 5,
) -> int:
    lines = wrap_text(text, fnt, rect.width)
    y = rect.y
    for line in lines:
        rendered = fnt.render(line, True, color)
        x = rect.centerx - rendered.get_width() // 2 if center else rect.x
        surface.blit(rendered, (x, y))
        y += rendered.get_height() + line_gap
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
