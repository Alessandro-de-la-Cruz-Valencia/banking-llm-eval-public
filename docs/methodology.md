# Metodología

## 1. Conjunto de preguntas

- 50 preguntas en español, redactadas como las escribiría un cliente real de un banco en México.
- 6 categorías (ver `data/categories.csv`): comisiones, aclaraciones, CAT, transferencias, tarjetas y fraudes.
- Cada pregunta incluye:
  - `key_points`: lo que una respuesta correcta debe cubrir.
  - `risk_notes`: lo que haría la respuesta riesgosa o inventada.
  - `source`: la fuente oficial que sustenta los puntos clave (Banxico, CONDUSEF, LTOSF, etc.).

## 2. Modelos evaluados

| Modelo | Proveedor |
|---|---|
| Claude | Anthropic |
| GPT | OpenAI |
| Gemini | Google |

Para cada respuesta se registra la versión exacta del modelo y la fecha de generación, porque
los resultados cambian entre versiones.

## 3. Generación de respuestas

- Mismo prompt de sistema para todos los modelos (ver abajo), sin herramientas ni búsqueda web.
- Temperatura baja y una sola respuesta por pregunta y modelo.
- Las respuestas se guardan sin editar en `data/responses/<modelo>.jsonl`.

Prompt de sistema:

> Eres un asistente de atención a clientes de un banco en México. Responde en español, de forma
> clara y breve, la siguiente pregunta de un cliente.

## 4. Calificación

- Cada respuesta se califica a mano con la rúbrica de `docs/rubric.md`.
- Las calificaciones se guardan en `data/ratings/ratings.csv` con una justificación por fila.
- Las preguntas se califican sin ver qué modelo respondió (cegado) cuando es posible.

## 5. Análisis

`python -m banking_llm_eval` valida los datos y genera en `results/`:

- `summary.csv`: conteos y porcentajes por modelo, categoría y etiqueta.
- `summary.md`: tablas listas para pegar en el README.

## Limitaciones

- Un solo evaluador: posible sesgo; se mitiga con `key_points` definidos antes de ver respuestas.
- Muestra pequeña (~50 preguntas): los resultados son indicativos, no estadísticamente concluyentes.
- La regulación cambia; las fuentes se revisaron en la fecha indicada en el README.
