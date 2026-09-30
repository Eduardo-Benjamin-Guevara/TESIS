# Sprint 11 — Asistente inteligente (IA)

## Objetivo

Incorporar al sistema de control de alimentos una **inteligencia artificial
conversacional en español** que responda con datos reales del inventario y
ayude a los usuarios a conocer el estado del almacén y a usar el sistema.

## Qué se implementó

Un **chatbot accesible desde `/ia/`** (menú *Inteligencia artificial →
Asistente*) con dos modos de funcionamiento:

### 1. Asistente integrado (modelo entrenado)

- **Clasificador de intenciones** TF-IDF + similitud de coseno implementado en
  `app/services/ia_service.py`, entrenado con un **corpus de frases en
  español** del dominio (`CORPUS`). El modelo se entrena al arrancar
  (`entrenar()`) y queda cacheado por proceso (`obtener_modelo()`), apto para
  serverless por no requerir librerías pesadas.
- Reconoce **13 intenciones**: saludo, despedida, gracias, ayuda, resumen,
  stock_bajo, vencimiento, vencidos, recomendaciones, categorias, alimento,
  movimientos, alertas y sistema (uso del sistema).
- **Respuestas con datos reales**: cada intención consulta los servicios del
  dominio (reportes, alertas, recomendaciones, categorías, trazabilidad) para
  responder, por ejemplo, *"¿qué alimentos tienen stock bajo?"* devuelve la
  lista real con stock y mínimo.
- **Base de conocimiento**: guía de uso de las 11 funciones del sistema
  (registrar alimentos, entradas/salidas, lotes, usuarios, exportar reportes,
  QR, trazabilidad, alertas, recomendaciones).

### 2. Conector a IA externa (opcional)

- Si se configura `IA_API_KEY` (API compatible con OpenAI / Chat Completions),
  las preguntas se envían a la IA externa acompañadas de un **contexto del
  inventario** (KPIs actuales). Si falla o no está configurada, se usa el
  asistente integrado. Sin costo cuando no se configura.

### 3. Interfaz

- Página completa del chat (`app/templates/ia/chat.html`) con chips de
  preguntas rápidas, burbujas de mensaje y entrada por Enter.
- JavaScript con soporte CSRF (`public/static/js/ia.js`).
- Ruta JSON `POST /ia/api/preguntar` (`app/routes/ia.py`).

## Variables de entorno nuevas

| Variable | Descripción | Defecto |
|---|---|---|
| `IA_API_KEY` | Clave de la IA externa (vacío = solo integrada) | *(vacío)* |
| `IA_API_URL` | Endpoint Chat Completions (compatible OpenAI) | `https://api.openai.com/v1/chat/completions` |
| `IA_API_MODEL` | Modelo de la IA externa | `gpt-4o-mini` |

## Pruebas

Nuevo módulo `tests/test_ia.py` con **17 pruebas**: entrenamiento del modelo,
clasificación de intenciones, respuestas con datos reales (resumen, stock
bajo, alimento específico, vencimientos), endpoint HTTP (página + API JSON,
con/sin mensaje), fallback de consulta desconocida y comportamiento de la IA
externa sin clave.

**Total de la suite: 124/124 pruebas aprobadas (100%).**

## Verificación

- `python -m pytest` → 124 passed.
- `python generar_reportes.py` → `RESUMEN: 124 aprobadas | 0 fallidas | 100%`.
- Prueba manual: iniciar sesión, abrir `Asistente` y hacer las preguntas de
  ejemplo.