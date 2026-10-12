"""Generación de summary.csv y summary.md."""

from __future__ import annotations

import csv
from pathlib import Path

from . import LABELS
from .score import Row


def write_csv(rows: list[Row], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "category", "total", *LABELS, *(f"pct_{l}" for l in LABELS)])
        for row in rows:
            writer.writerow([
                row.model, row.category, row.total,
                *(row.counts[l] for l in LABELS),
                *(f"{row.pct(l):.1f}" for l in LABELS),
            ])


def to_markdown(rows: list[Row], categories: dict[str, str]) -> str:
    if not rows:
        return "# Resumen\n\nAún no hay calificaciones en `data/ratings/ratings.csv`.\n"

    header = "| Categoría | n | " + " | ".join(LABELS) + " |"
    divider = "|---|---:|" + "---:|" * len(LABELS)
    lines = ["# Resumen", ""]

    totals = [r for r in rows if r.category == "TOTAL"]
    lines += ["## Por modelo", "", header.replace("Categoría", "Modelo"), divider]
    for r in totals:
        lines.append(f"| {r.model} | {r.total} | " + " | ".join(f"{r.pct(l):.0f}%" for l in LABELS) + " |")

    for model in dict.fromkeys(r.model for r in rows):
        lines += ["", f"## {model} por categoría", "", header, divider]
        for r in rows:
            if r.model == model and r.category != "TOTAL":
                name = categories.get(r.category, r.category)
                lines.append(f"| {name} | {r.total} | " + " | ".join(f"{r.pct(l):.0f}%" for l in LABELS) + " |")
    return "\n".join(lines) + "\n"


def examples_markdown(ratings: list, questions: dict, responses: list[dict],
                      labels: tuple[str, ...] = ("riesgosa", "inventada")) -> str:
    """Lista las respuestas con las etiquetas más graves, para documentar hallazgos."""
    text = {(r["question_id"], r["model"]): r["response"] for r in responses}
    lines = ["# Ejemplos de errores", ""]
    found = False
    for label in labels:
        selected = [r for r in ratings if r.label == label]
        if not selected:
            continue
        found = True
        lines += [f"## {label} ({len(selected)})", ""]
        for r in sorted(selected, key=lambda r: (r.question_id, r.model)):
            q = questions[r.question_id]
            response = text.get((r.question_id, r.model), "_(respuesta no encontrada)_")
            quoted = "\n".join(f"> {line}" if line else ">" for line in response.splitlines())
            lines += [
                f"### {r.question_id} · {r.model}",
                "",
                f"**Pregunta:** {q.question}",
                "",
                quoted,
                "",
                f"**Por qué:** {r.rationale}",
                "",
            ]
    if not found:
        lines.append("Aún no hay respuestas etiquetadas como " + " o ".join(labels) + ".")
    return "\n".join(lines).rstrip() + "\n"
