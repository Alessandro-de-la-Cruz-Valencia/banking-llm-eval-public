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
