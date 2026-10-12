"""Calificación manual a ciegas de las respuestas.

Uso:
    python -m banking_llm_eval.rate --rater <tu_nombre>

Muestra cada respuesta pendiente sin decir qué modelo la generó, junto con los
puntos clave y riesgos de la pregunta, y guarda la etiqueta y la justificación
en data/ratings/ratings.csv. Se puede salir con "q" y continuar después.
"""

from __future__ import annotations

import argparse
import csv
import random
import textwrap
from collections.abc import Callable
from pathlib import Path

from . import LABELS
from .data import load_categories, load_questions, load_ratings, load_responses

PROMPT = "Etiqueta [" + " ".join(f"{i}={l}" for i, l in enumerate(LABELS, start=1)) + ", q=salir]: "


def pending_items(responses: list[dict], rated: set[tuple[str, str]], seed: int) -> list[dict]:
    items = [r for r in responses if (r["question_id"], r["model"]) not in rated]
    random.Random(seed).shuffle(items)
    return items


def ask_label(ask: Callable[[str], str]) -> str | None:
    while True:
        answer = ask(PROMPT).strip().lower()
        if answer == "q":
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(LABELS):
            return LABELS[int(answer) - 1]
        if answer in LABELS:
            return answer


def ask_rationale(ask: Callable[[str], str]) -> str:
    while True:
        rationale = ask("Justificación: ").strip()
        if rationale:
            return rationale


def main(argv: list[str] | None = None, ask: Callable[[str], str] = input) -> int:
    parser = argparse.ArgumentParser(description="Califica las respuestas pendientes a ciegas.")
    parser.add_argument("--rater", required=True)
    parser.add_argument("--seed", type=int, default=42, help="Semilla del orden aleatorio")
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    categories = load_categories(args.data / "categories.csv")
    questions = load_questions(args.data / "questions.csv", categories)
    ratings_path = args.data / "ratings" / "ratings.csv"
    rated = {(r.question_id, r.model) for r in load_ratings(ratings_path, questions)}
    items = pending_items(load_responses(args.data / "responses"), rated, args.seed)

    print(f"{len(items)} respuestas pendientes de calificar.\n")
    with ratings_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        for i, item in enumerate(items, start=1):
            q = questions[item["question_id"]]
            print("=" * 72)
            print(f"[{i}/{len(items)}] {q.id} · {categories[q.category]}")
            print(f"\nPregunta: {q.question}\n")
            print(textwrap.indent(item["response"], "  │ "))
            print(f"\nPuntos clave: {q.key_points}")
            print(f"Riesgos: {q.risk_notes}\n")

            label = ask_label(ask)
            if label is None:
                break
            writer.writerow([q.id, item["model"], label, ask_rationale(ask), args.rater])
            f.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
