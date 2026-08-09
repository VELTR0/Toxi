from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


MASTERY_TARGET = 3


def _progress_path() -> Path:
    if os.name == "nt" and os.environ.get("APPDATA"):
        base = Path(os.environ["APPDATA"]) / "Toxi"
    else:
        base = Path.home() / ".toxi"
    base.mkdir(parents=True, exist_ok=True)
    return base / "progress.json"


class ProgressStore:
    def __init__(self, question_ids: list[str]) -> None:
        self.path = _progress_path()
        self.question_ids = question_ids
        self.data: dict[str, Any] = self._load()
        self._ensure_questions()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"global_score": 0, "questions": {}}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("progress root must be an object")
            data.setdefault("global_score", 0)
            data.setdefault("questions", {})
            return data
        except (OSError, json.JSONDecodeError, ValueError):
            return {"global_score": 0, "questions": {}}

    def _ensure_questions(self) -> None:
        questions = self.data.setdefault("questions", {})
        for question_id in self.question_ids:
            questions.setdefault(question_id, {"points": 0, "attempts": 0})
        self.save()

    def save(self) -> None:
        temp = self.path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)
        temp.replace(self.path)

    def points(self, question_id: str) -> int:
        return int(self.data["questions"][question_id].get("points", 0))

    def attempts(self, question_id: str) -> int:
        return int(self.data["questions"][question_id].get("attempts", 0))

    @property
    def global_score(self) -> int:
        return int(self.data.get("global_score", 0))

    def record_result(self, question_id: str, correct: bool) -> None:
        entry = self.data["questions"][question_id]
        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        if correct:
            entry["points"] = min(MASTERY_TARGET, int(entry.get("points", 0)) + 1)
            self.data["global_score"] = self.global_score + 1
        self.save()

    def pending_ids(self) -> list[str]:
        return [qid for qid in self.question_ids if self.points(qid) < MASTERY_TARGET]

    def learned_count(self) -> int:
        return sum(self.points(qid) >= MASTERY_TARGET for qid in self.question_ids)

    def reset(self) -> None:
        self.data = {"global_score": 0, "questions": {}}
        self._ensure_questions()
