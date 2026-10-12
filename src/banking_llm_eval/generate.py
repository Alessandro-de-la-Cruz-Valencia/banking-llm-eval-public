"""Genera respuestas de los modelos para cada pregunta.

Uso:
    python -m banking_llm_eval.generate --provider anthropic --model <id> --name claude
    python -m banking_llm_eval.generate --provider openai --model <id> --name gpt
    python -m banking_llm_eval.generate --provider gemini --model <id> --name gemini

Las API keys se leen de ANTHROPIC_API_KEY, OPENAI_API_KEY y GEMINI_API_KEY.
Las respuestas se agregan a data/responses/<name>.jsonl; las preguntas que ya
tienen respuesta se omiten, así que el script se puede reanudar.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .data import load_categories, load_questions, load_responses

SYSTEM_PROMPT = (
    "Eres un asistente de atención a clientes de un banco en México. "
    "Responde en español, de forma clara y breve, la siguiente pregunta de un cliente."
)
MAX_TOKENS = 1024
API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def build_request(provider: str, model: str, question: str, api_key: str,
                  temperature: float | None) -> tuple[str, dict, dict]:
    """Devuelve (url, headers, body) para el proveedor indicado."""
    if provider == "anthropic":
        body = {
            "model": model,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": question}],
        }
        if temperature is not None:
            body["temperature"] = temperature
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        return "https://api.anthropic.com/v1/messages", headers, body

    if provider == "openai":
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        }
        if temperature is not None:
            body["temperature"] = temperature
        headers = {"Authorization": f"Bearer {api_key}"}
        return "https://api.openai.com/v1/chat/completions", headers, body

    if provider == "gemini":
        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": question}]}],
        }
        if temperature is not None:
            body["generationConfig"] = {"temperature": temperature}
        headers = {"x-goog-api-key": api_key}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        return url, headers, body

    raise ValueError(f"Proveedor desconocido: {provider}")


def parse_response(provider: str, payload: dict) -> tuple[str, str | None]:
    """Extrae (texto, versión_del_modelo) de la respuesta JSON del proveedor."""
    if provider == "anthropic":
        text = "".join(b.get("text", "") for b in payload["content"] if b.get("type") == "text")
        return text.strip(), payload.get("model")
    if provider == "openai":
        return payload["choices"][0]["message"]["content"].strip(), payload.get("model")
    if provider == "gemini":
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip(), payload.get("modelVersion")
    raise ValueError(f"Proveedor desconocido: {provider}")


def call_api(url: str, headers: dict, body: dict, retries: int = 4) -> dict:
    data = json.dumps(body).encode("utf-8")
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Content-Type": "application/json", **headers},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            retryable = e.code == 429 or e.code >= 500
            if not retryable or attempt == retries:
                detail = e.read().decode("utf-8", "replace")[:500]
                raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            if attempt == retries:
                raise RuntimeError(f"Error de red: {e.reason}") from e
        time.sleep(2 ** (attempt + 1))
    raise AssertionError("inalcanzable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera respuestas de un modelo para todas las preguntas.")
    parser.add_argument("--provider", required=True, choices=sorted(API_KEY_ENV))
    parser.add_argument("--model", required=True, help="ID exacto del modelo en la API del proveedor")
    parser.add_argument("--name", required=True, help="Nombre corto para reportes, p. ej. claude, gpt, gemini")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--no-temperature", action="store_true",
                        help="No enviar temperatura (para modelos que no la aceptan)")
    parser.add_argument("--limit", type=int, help="Procesar solo N preguntas (para pruebas)")
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args(argv)

    api_key = os.environ.get(API_KEY_ENV[args.provider])
    if not api_key:
        print(f"Falta la variable de entorno {API_KEY_ENV[args.provider]}", file=sys.stderr)
        return 1

    categories = load_categories(args.data / "categories.csv")
    questions = load_questions(args.data / "questions.csv", categories)
    responses_dir = args.data / "responses"
    done = {r["question_id"] for r in load_responses(responses_dir) if r["model"] == args.name}
    pending = [q for q in questions.values() if q.id not in done][: args.limit]
    temperature = None if args.no_temperature else args.temperature

    out_path = responses_dir / f"{args.name}.jsonl"
    print(f"{len(pending)} preguntas pendientes para {args.name} ({args.model})")
    with out_path.open("a", encoding="utf-8") as out:
        for i, q in enumerate(pending, start=1):
            url, headers, body = build_request(args.provider, args.model, q.question, api_key, temperature)
            text, version = parse_response(args.provider, call_api(url, headers, body))
            record = {
                "question_id": q.id,
                "model": args.name,
                "provider": args.provider,
                "model_version": version or args.model,
                "response": text,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "params": {"temperature": temperature, "max_tokens": MAX_TOKENS},
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(pending)}] {q.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
