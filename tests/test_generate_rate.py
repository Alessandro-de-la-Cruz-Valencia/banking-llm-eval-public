import unittest

from banking_llm_eval.data import Question, Rating
from banking_llm_eval.generate import SYSTEM_PROMPT, build_request, parse_response
from banking_llm_eval.rate import ask_label, pending_items
from banking_llm_eval.report import examples_markdown


class BuildRequestTest(unittest.TestCase):
    def test_anthropic(self):
        url, headers, body = build_request("anthropic", "m", "¿Qué es el CAT?", "k", 0.0)
        self.assertTrue(url.endswith("/v1/messages"))
        self.assertEqual(headers["x-api-key"], "k")
        self.assertEqual(body["system"], SYSTEM_PROMPT)
        self.assertEqual(body["messages"][0]["content"], "¿Qué es el CAT?")

    def test_openai_without_temperature(self):
        _, headers, body = build_request("openai", "m", "q", "k", None)
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertNotIn("temperature", body)
        self.assertEqual(body["messages"][0]["role"], "system")

    def test_gemini(self):
        url, headers, body = build_request("gemini", "gm", "q", "k", 0.0)
        self.assertIn("/models/gm:generateContent", url)
        self.assertEqual(body["generationConfig"]["temperature"], 0.0)

    def test_unknown_provider(self):
        with self.assertRaises(ValueError):
            build_request("otro", "m", "q", "k", None)


class ParseResponseTest(unittest.TestCase):
    def test_anthropic(self):
        payload = {"model": "v1", "content": [{"type": "text", "text": " Hola "}]}
        self.assertEqual(parse_response("anthropic", payload), ("Hola", "v1"))

    def test_openai(self):
        payload = {"model": "v2", "choices": [{"message": {"content": "Hola"}}]}
        self.assertEqual(parse_response("openai", payload), ("Hola", "v2"))

    def test_gemini(self):
        payload = {"modelVersion": "v3",
                   "candidates": [{"content": {"parts": [{"text": "Ho"}, {"text": "la"}]}}]}
        self.assertEqual(parse_response("gemini", payload), ("Hola", "v3"))


class RateTest(unittest.TestCase):
    def test_pending_skips_rated_and_is_deterministic(self):
        responses = [{"question_id": f"Q-{i}", "model": "m"} for i in range(10)]
        rated = {("Q-0", "m")}
        first = pending_items(responses, rated, seed=1)
        self.assertEqual(len(first), 9)
        self.assertEqual(first, pending_items(responses, rated, seed=1))

    def test_ask_label_accepts_number_name_and_quit(self):
        answers = iter(["x", "2"])
        self.assertEqual(ask_label(lambda _: next(answers)), "incompleta")
        self.assertEqual(ask_label(lambda _: "riesgosa"), "riesgosa")
        self.assertIsNone(ask_label(lambda _: "q"))


class ExamplesTest(unittest.TestCase):
    def test_lists_only_severe_labels(self):
        questions = {"A-1": Question("A-1", "cat", "¿Pregunta?", "", "", "")}
        ratings = [Rating("A-1", "m1", "riesgosa", "da el NIP", "x"),
                   Rating("A-1", "m2", "correcta", "ok", "x")]
        responses = [{"question_id": "A-1", "model": "m1", "response": "Dame tu NIP"}]
        md = examples_markdown(ratings, questions, responses)
        self.assertIn("> Dame tu NIP", md)
        self.assertIn("da el NIP", md)
        self.assertNotIn("m2", md)


if __name__ == "__main__":
    unittest.main()
