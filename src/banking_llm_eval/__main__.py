"""Uso: python -m banking_llm_eval [--data data] [--out results]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .data import DataError, load_categories, load_questions, load_ratings
from .report import to_markdown, write_csv
from .score import summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calcula resultados por modelo y categoría.")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args(argv)

    try:
        categories = load_categories(args.data / "categories.csv")
        questions = load_questions(args.data / "questions.csv", categories)
        ratings = load_ratings(args.data / "ratings" / "ratings.csv", questions)
    except DataError as e:
        print(f"Error en los datos: {e}", file=sys.stderr)
        return 1

    rows = summarize(ratings, questions)
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out / "summary.csv")
    markdown = to_markdown(rows, categories)
    (args.out / "summary.md").write_text(markdown, encoding="utf-8")

    print(f"{len(questions)} preguntas, {len(ratings)} calificaciones.")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
