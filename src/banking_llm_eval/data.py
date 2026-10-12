"""Carga y validación de los archivos de datos."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from . import LABELS


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    question: str
    key_points: str
    risk_notes: str
    source: str


@dataclass(frozen=True)
class Rating:
    question_id: str
    model: str
    label: str
    rationale: str
    rater: str


class DataError(ValueError):
    """Error de formato o de consistencia en los datos."""


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_categories(path: Path) -> dict[str, str]:
    """Devuelve {id_categoria: nombre}."""
    return {row["id"]: row["name"] for row in _read_csv(path)}


def load_questions(path: Path, categories: dict[str, str]) -> dict[str, Question]:
    questions: dict[str, Question] = {}
    for row in _read_csv(path):
        q = Question(**row)
        if q.id in questions:
            raise DataError(f"Pregunta duplicada: {q.id}")
        if q.category not in categories:
            raise DataError(f"{q.id}: categoría desconocida '{q.category}'")
        questions[q.id] = q
    return questions


def load_ratings(path: Path, questions: dict[str, Question]) -> list[Rating]:
    ratings: list[Rating] = []
    seen: set[tuple[str, str]] = set()
    for line_no, row in enumerate(_read_csv(path), start=2):
        r = Rating(**{k: (v or "").strip() for k, v in row.items()})
        where = f"{path.name}:{line_no}"
        if r.question_id not in questions:
            raise DataError(f"{where}: pregunta desconocida '{r.question_id}'")
        if r.label not in LABELS:
            raise DataError(f"{where}: etiqueta '{r.label}' no es una de {LABELS}")
        if not r.rationale:
            raise DataError(f"{where}: falta la justificación (rationale)")
        key = (r.question_id, r.model)
        if key in seen:
            raise DataError(f"{where}: calificación duplicada para {key}")
        seen.add(key)
        ratings.append(r)
    return ratings


def load_responses(directory: Path) -> list[dict]:
    """Lee todas las respuestas de data/responses/*.jsonl."""
    responses: list[dict] = []
    for path in sorted(directory.glob("*.jsonl")):
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    responses.append(json.loads(line))
    return responses
