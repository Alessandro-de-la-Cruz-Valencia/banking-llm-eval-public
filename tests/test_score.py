import tempfile
import unittest
from pathlib import Path

from banking_llm_eval.data import DataError, Question, Rating, load_ratings
from banking_llm_eval.report import to_markdown
from banking_llm_eval.score import summarize

QUESTIONS = {
    "A-1": Question("A-1", "cat", "q", "", "", ""),
    "A-2": Question("A-2", "cat", "q", "", "", ""),
    "B-1": Question("B-1", "fraudes", "q", "", "", ""),
}


class SummarizeTest(unittest.TestCase):
    def test_counts_by_category_and_total(self):
        ratings = [
            Rating("A-1", "claude", "correcta", "ok", "x"),
            Rating("A-2", "claude", "inventada", "ok", "x"),
            Rating("B-1", "claude", "riesgosa", "ok", "x"),
        ]
        rows = {(r.model, r.category): r for r in summarize(ratings, QUESTIONS)}

        self.assertEqual(rows[("claude", "cat")].total, 2)
        self.assertEqual(rows[("claude", "cat")].pct("correcta"), 50.0)
        self.assertEqual(rows[("claude", "TOTAL")].counts["riesgosa"], 1)
        self.assertEqual(rows[("claude", "TOTAL")].total, 3)

    def test_empty_ratings_report(self):
        self.assertIn("Aún no hay calificaciones", to_markdown([], {}))


class LoadRatingsTest(unittest.TestCase):
    def _load(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ratings.csv"
            path.write_text("question_id,model,label,rationale,rater\n" + body, encoding="utf-8")
            return load_ratings(path, QUESTIONS)

    def test_rejects_unknown_label(self):
        with self.assertRaises(DataError):
            self._load("A-1,claude,regular,ok,x\n")

    def test_rejects_duplicate(self):
        with self.assertRaises(DataError):
            self._load("A-1,claude,correcta,ok,x\nA-1,claude,correcta,ok,x\n")

    def test_requires_rationale(self):
        with self.assertRaises(DataError):
            self._load("A-1,claude,correcta,,x\n")


if __name__ == "__main__":
    unittest.main()
