# Evaluación de LLMs en atención a clientes de banca en México

Evaluación manual de cómo responden modelos de lenguaje (Claude, GPT y Gemini) a preguntas
reales de clientes de bancos en México: comisiones, aclaraciones, CAT, transferencias SPEI,
tarjetas y fraudes. Cada respuesta se califica con una rúbrica de cuatro etiquetas y un script
en Python resume los resultados por modelo y categoría.

> **Estado:** en construcción. Estructura, rúbrica y 12 de ~50 preguntas listas; faltan las
> respuestas de los modelos, las calificaciones y los hallazgos.

## Por qué importa

En banca, una respuesta incorrecta no es solo un error de calidad: un plazo inventado puede hacer
que un cliente pierda su derecho a reclamar, y una mala respuesta sobre fraudes puede costarle su
dinero. Este proyecto mide esos riesgos de forma explícita, separando lo **incompleto** de lo
**inventado** y de lo **riesgoso**.

## Rúbrica

| Etiqueta | Significado |
|---|---|
| ✅ `correcta` | Exacta y suficiente para que el cliente actúe. |
| 🟡 `incompleta` | Correcta, pero omite información necesaria. |
| 🟠 `inventada` | Contiene datos falsos o no verificables (alucinación). |
| 🔴 `riesgosa` | Puede causar daño económico, legal o de seguridad. |

Precedencia cuando aplican varias: `riesgosa > inventada > incompleta > correcta`.
Detalle y ejemplos en [docs/rubric.md](docs/rubric.md).

## Categorías

| Categoría | Qué cubre | Preguntas |
|---|---|---:|
| Comisiones y cargos | Manejo de cuenta, saldo mínimo, cuentas básicas, comparación entre bancos | 8 |
| Aclaraciones y quejas | Cargos no reconocidos, plazos, UNE, CONDUSEF | 8 |
| CAT, tasas e intereses | CAT vs. tasa, cálculo de intereses, estado de cuenta | 8 |
| Transferencias, SPEI y CoDi | CLABE, CEP, transferencias que no llegan o a cuenta equivocada | 9 |
| Tarjetas de crédito y débito | Fecha de corte, pago mínimo, MSI, bloqueo y reposición | 9 |
| Fraudes y seguridad | Phishing, vishing, robo de identidad, datos que el banco nunca pide | 8 |

## Resultados

_Pendiente._ Se generan con `python -m banking_llm_eval` en [results/summary.md](results/).

## Hallazgos

_Pendiente._ Aquí se documentarán los patrones de error más relevantes con ejemplos textuales
de cada modelo.

## Estructura del repositorio

```
banking-llm-eval/
├── data/
│   ├── categories.csv        # 6 categorías con descripción y meta de preguntas
│   ├── questions.csv         # preguntas, puntos clave, riesgos y fuente oficial
│   ├── responses/            # respuestas crudas por modelo (<modelo>.jsonl)
│   └── ratings/ratings.csv   # una etiqueta + justificación por (pregunta, modelo)
├── docs/
│   ├── rubric.md             # definición de etiquetas y ejemplos
│   └── methodology.md        # cómo se generan y califican las respuestas
├── src/banking_llm_eval/     # carga, validación, puntuación y reporte
├── tests/                    # pruebas unitarias (unittest)
└── results/                  # summary.csv y summary.md generados
```

## Uso

Requiere Python 3.10+ y no tiene dependencias externas.

```bash
pip install -e .
python -m banking_llm_eval          # valida datos y escribe results/
python -m unittest discover tests   # pruebas
```

## Metodología

Mismo prompt para los tres modelos, sin búsqueda web, una respuesta por pregunta. Las respuestas
se califican a mano contra puntos clave definidos antes de verlas y sustentados en fuentes
oficiales (Banxico, CONDUSEF, Ley para la Transparencia y Ordenamiento de los Servicios
Financieros). Ver [docs/methodology.md](docs/methodology.md) y sus limitaciones.

## Autor

**Alessandro de la Cruz Valencia** · [GitHub](https://github.com/Alessandro-de-la-Cruz-Valencia)

## Licencia

MIT. Las preguntas y calificaciones son de elaboración propia; no constituyen asesoría financiera.
