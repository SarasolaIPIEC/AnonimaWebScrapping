
# ipc-ushuaia — Documentación guía (solo textos)

Este repositorio reúne **documentos guía** para orientar a Copilot/Codex y a las personas del equipo sobre cómo construir un **índice local de precios** estilo CBA para **Ushuaia**.

## Documentos clave
- `AGENTS.md` — Cómo debe operar Copilot (autonomía, sin plazos, trazabilidad).
- `CONTEXT.md` — Objetivos, fuente de precios y lineamientos esenciales.
- `PROMPTS.md` — Prompts secuenciales con encabezado de pegamento.
- `SCRAPING_GUIDE.md` — Guía conceptual para recolección de precios.
- `NORMALIZATION_GUIDE.md` — Criterios de normalización y unidades base.
- `DATA_MODEL_GUIDE.md` — Modelo de datos conceptual y exportables.
- `REPORTING_GUIDE.md` — Salidas, KPIs, narrativa y buenas prácticas.
- `RUNBOOK.md` — Flujo operativo, validaciones y recuperación.
- `METHODOLOGY.md` — Metodología resumida (CBA, AE=3,09, índice base=100).
- `FAQ.md` — Preguntas frecuentes.

> Estos archivos son **guías escritas**. No incluyen módulos de código. Los esqueletos o implementaciones se generarán solo cuando un prompt lo solicite explícitamente.

## Instalación

1. Posicionarse en la carpeta `ipc-ushuaia/`.
2. Instalar dependencias con `pip install -r requirements.txt`.
3. Instalar Playwright y el navegador Chromium:

```bash
pip install playwright
playwright install chromium
```

## Configuración

- Copiar `.env.example` a `.env` y completar valores como `BRANCH`, `HEADLESS`, `MAX_RETRIES`, `DELAYS`, `USER_AGENT`, `OUTPUT_DIRS`, `API_KEY` y `EMAIL`.
- Ajustar `config.toml` según el entorno; el archivo define opciones como `branch`, `headless`, `delays`, `max_retries`, `user_agent` y `output_dirs`.
- El `USER_AGENT` predeterminado identifica al proyecto como `ipc-ushuaia-bot/1.0 (+https://github.com/AnonimaWebScrapping)` y puede personalizarse en `.env`.

## Buenas prácticas de scraping

- Respetar `robots.txt` y los términos de uso del sitio antes de realizar cualquier solicitud.
- Introducir delays aleatorios entre acciones de scraping para minimizar la carga sobre el servidor.
- Mantener credenciales y claves en `.env` (ignorado en control de versiones) y evitar registrarlas en logs.

## Ejecución

Ejecutar la aplicación con:

```bash
python -m src.cli run
```

El subcomando `run` dispara el flujo completo utilizando la configuración cargada.

## Jerarquía de carpetas

- `src/` — Código fuente para scraping, normalización e índices.
- `data/` — Entradas y salidas persistentes del proceso.
- `docs/` — Documentos guía y metodología.
- `examples/` — Ejemplos de uso y prototipos.
- `tests/` — Casos de prueba automáticos.
- `ipc-ushuaia/` — Dependencias y recursos específicos del proyecto.

## Flujo de datos

1. Los módulos de `src/` consultan precios de La Anónima.
2. La información se normaliza (unidades y promociones) y se guarda en `data/`.
3. Se calculan índices y métricas para generar reportes reutilizables.

## Comandos principales

- `python -m src.cli run` — Ejecuta el flujo completo.
- `pytest` — Corre los tests del proyecto.

## Decisiones abiertas

- Definir el esquema de persistencia para históricos de precios.
- Establecer la estrategia de autenticación y rotación de claves API.
- Completar y versionar el módulo CLI definitivo.

