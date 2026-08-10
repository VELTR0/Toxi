"""Question bank derived from the provided toxicology study notes."""

from .questions import QUESTIONS


def validate_questions() -> None:
    ids = set()
    allowed = {
        "sword_arena",
        "maze_portals",
        "platform_gates",
        "lab_catcher",
        "comet_click",
        "pokemon_battle",
        "sole_man",
        "quick_draw",
    }
    for q in QUESTIONS:
        assert q["id"] not in ids, f"duplicate question id: {q['id']}"
        ids.add(q["id"])
        assert len(q["answers"]) == 3
        assert 0 <= q["correct"] < len(q["answers"])
        assert len(q["variants"]) == 2, f"{q['id']} must have exactly two variants"
        assert set(q["variants"]).issubset(allowed)


validate_questions()
