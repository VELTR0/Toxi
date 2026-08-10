import argparse

from toxi.game import ToxiGame
from toxi.microgames import MICROGAME_TYPES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Toxi - Toxicology Microgames")
    parser.add_argument(
        "--debug-microgame",
        choices=sorted(MICROGAME_TYPES),
        help="Startet direkt ein bestimmtes Microgame. Der Lernfortschritt wird dabei nicht verändert.",
    )
    parser.add_argument(
        "--debug-question",
        help="Optionale Frage-ID für den Debug-Start. Benötigt --debug-microgame.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        ToxiGame(
            debug_microgame=args.debug_microgame,
            debug_question_id=args.debug_question,
        ).run()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
