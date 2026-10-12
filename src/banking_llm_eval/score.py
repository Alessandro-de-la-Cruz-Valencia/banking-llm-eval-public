"""Cálculo de resultados por modelo y categoría."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from . import LABELS
from .data import Question, Rating


@dataclass(frozen=True)
class Row:
    model: str
    category: str  # "TOTAL" para el agregado del modelo
    total: int
    counts: dict[str, int]

    def pct(self, label: str) -> float:
        return 100 * self.counts[label] / self.total if self.total else 0.0


def summarize(ratings: list[Rating], questions: dict[str, Question]) -> list[Row]:
    """Cuenta etiquetas por (modelo, categoría) y por modelo en total."""
    groups: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for r in ratings:
        category = questions[r.question_id].category
        groups[(r.model, category)][r.label] += 1
        groups[(r.model, "TOTAL")][r.label] += 1

    rows = []
    for (model, category), counter in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] == "TOTAL", kv[0][1])):
        counts = {label: counter.get(label, 0) for label in LABELS}
        rows.append(Row(model, category, sum(counts.values()), counts))
    return rows
