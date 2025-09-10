# ERRORS.md — Gestión de errores

## DOM
- Cambios en la estructura del sitio pueden invalidar selectores y causar fallos de parseo.
- **Estrategia:** fallback con palabras clave alternativas y heurísticas.
- **Módulo:** `src/parser.py`.

## OOS (Out of Stock)
- Productos listados sin stock afectan la cobertura de la canasta.
- **Estrategia:** fallback mediante sustituciones documentadas y registro de métricas.
- **Módulos:** `src/parser.py`, `src/metrics/telemetry.py`.

## Rate limiting
- Respuestas HTTP 429 u otros límites de frecuencia del servidor.
- **Estrategia:** backoff exponencial para reintentos escalonados.
- **Módulo:** `src/infra/retry.py` (`exponential_backoff`).

## Fallas persistentes del servicio
- Errores repetidos de red o HTTP 5xx que impiden avanzar.
- **Estrategia:** circuit breaker para pausar y reintentar luego de un enfriamiento.
- **Módulo:** `src/infra/retry.py` (`circuit_breaker`).
