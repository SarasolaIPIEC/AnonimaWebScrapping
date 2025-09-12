A continuación te dejo un plan de trabajo “production-grade” end-to-end, con subtareas largas y seccionadas, autonomía de diseño, criterios de “listo”, riesgos y mitigaciones. Ya dejé el reporte con filtros/ordenamiento funcionando; el resto queda propuesto para que lo ejecute todo acá mismo si querés.

Resumen de Cambios Hechos

Reporte interactivo: filtros combinables por texto/categoría/brand_tier/CBA, rango de precio, orden por precio y unitario, estado “Mostrando X de Y”, responsive y accesible básico.
src/reporting/render.py:139
src/reporting/render.py:198
src/reporting/render.py:411
src/reporting/render.py:460
src/reporting/render.py:514
src/reporting/render.py:521
src/reporting/render.py:534

1. Ingesta & Resiliencia

Objetivo: unir CSVs por categoría y robustecer la extracción respetando el sitio.
Subtareas
Lector de by_category/\*.csv: merge con columnas mínimas period,item_id,url,title,brand_tier,cba_flag,category. Dedup por (period,item_id,url).
Verificación previa de PDP: para cada URL, abrir con Playwright sólo tras fijar sucursal (CP 9410). Retry con backoff exponencial y jitter; timeouts explícitos.
Ritmo: sleeps aleatorios cortos entre acciones, user-agent declarativo, headers limpios.
Fallbacks: si PDP falla o no tiene precio parseable, intentar segundo SKU de misma categoría/tier; logear sustitución y causa.
Implementación sugerida
Nuevo src/ingest/csv_input.py: función read_by_category(glob_pattern) -> List[rows] con normalización + dedup.
Hook en src/cli.py:cmd_run para preferir dataset externo si existe (sin romper el flujo actual).
src/site/utils.py: retry_with_backoff(fn, retries, base, jitter) y random_sleep(min_ms,max_ms).
src/site/branch.py: asegurar que toda navegación se haga luego de ensure_branch(...).
Criterios “listo”
Dataset único sin duplicados; PDP se abren con sucursal correcta; fallas transitorias recuperables; sustituciones registradas.
Riesgos/Mitigaciones
Bloqueos por ritmo: throttle y jitter configurables en config.toml.
Estructuras CSV heterogéneas: coerción y validaciones con logs de fila rechazada. 2) Parsing Unificado (PDP)

Objetivo: unificar extracción y normalización de presentación y precio final.
Subtareas
Campos: title_observed, price_final, promo_flag, in_stock, pack_text, url, timestamp.
Parse de presentación: g/kg; ml/L/cc; docena=12; multipack “xN 500 g”; fracciones “1/2 kg”.
Normalización: a base kg/l/unit; cálculo unit_price_base.
Outliers: reglas por categoría y unitario, configurable; marcar outlier_flag + razón.
Implementación sugerida
Extender src/normalize/units.py con reglas y tests para docena, fracciones y multipacks.
src/site/product.py: garantizar extracción de pack_text además de título/precio/stock.
src/normalize/pricing.py: soportar unit_price_base=None sin romper; redondeos consistentes.
Criterios “listo”
unit_price_base coherente en al menos 95% items de canasta; casos especiales etiquetados.
Riesgos/Mitigaciones
Títulos ruidosos: fallback a heurísticas secundarias y a name del catálogo. 3) Calidad de Datos (DQ)

Objetivo: medir cobertura y detectar anomalías automáticamente.
Subtareas
Cobertura mínima en cba_flag=si.
% faltantes por categoría y tier; reporte de causas (404, sin precio, OOS, bloqueo).
Anomalías vs mes previo: z-score/umbral en unit_price_base por item_id o por categoría-tipo.
Implementación sugerida
Nuevo src/quality/checks.py: run_dq_checks(breakdown, prev_breakdown, cfg) -> report.
Integrar a cmd_run: si DQ falla fuera de umbrales configurables, salir con código≠0 y evidenciar.
Persistir missing_reasons.csv por período (idempotente).
Criterios “listo”
Indicadores DQ calculados y reporte impreso; exit≠0 cuando corresponde o se justifica en log.
Riesgos/Mitigaciones
Mes previo inexistente: tolerar primer período; ajustar checks condicionales. 4) Cálculo Metodológico

Objetivo: costos por AE, CBA AE y familia, índice base=100, m/m e i.a., con trazabilidad.
Subtareas
Catálogo de cantidades por AE versionado; etiquetar basket_version.
CBA AE = suma; CBA familia = ×3,09 (configurable).
Serie estable en exports/series_cba.csv con period,cba_ae,cba_family,idx,mom,yoy.
Implementación sugerida
src/metrics/cba.py: ya suma; agregar manejo de basket_version y totalización por canasta vigente.
src/metrics/index.py: mantener lógica; guardar metadatos de cambios de canasta en exports/baskets.csv o anotar en JSONL.
Criterios “listo”
Reproducibilidad: mismo período + mismos CSV ⇒ mismos outputs; índices alineados a metodología.
Riesgos/Mitigaciones
Cambios de canasta: versionar y registrar impacto con diff de ítems. 5) Reporte Final (UX de Analista)

Objetivo: exploración fluida con datos ricos y comparaciones.
Subtareas
Tabla principal con columnas ampliadas: item_id, title_observed linkeado, brand_tier, cba_flag, base_unit, pack_size_value, unit_price_base, price_final, in_stock, sustitución/nota, category, cost_item_ae.
Vistas: KPIs (ya), Top aportes (ya), Top variaciones del mes (nuevo), comparación por tier dentro de categoría (mini tablas).
Accesibilidad y rendimiento con cientos de filas, progressive enhancement (ya).
Implementación sugerida
Ampliar write_breakdown para incluir brand_tier, cba_flag, category, pack_text, base_unit, pack_size_value cuando existan.
Añadir sección “Top variaciones” comparando con breakdown del período previo (orden desc).
Añadir comparativa “premium/estándar/segunda” por categoría (promedio unit_price_base por tier).
Criterios “listo”
Filtros y orden activos; comparaciones por tier operativas; sin afectar performance.
Riesgos/Mitigaciones
Datos faltantes: ocultar controles sin datos; placeholders en celdas. 6) Observabilidad & Auditoría

Objetivo: trazabilidad y evidencia reproducible.
Subtareas
Logging JSONL por etapa: timings, conteos, OOS, sustituciones, outliers, ratio válidos.
Evidencia: HTML crudo y screenshots; carpeta por período/fecha local en Ushuaia.
Resumen stdout: plaza, período, esperados/encontrados, faltantes, sustituciones, KPIs y paths.
Implementación sugerida
Extender json*log(...) en puntos clave de src/cli.py:cmd_run y src/site/\*.
Guardar causas de sustitución (objeto con prioridad, motivo, sku_anterior).
Criterios “listo”
Carpeta evidence/period_YYYY-MM-DD con HTML/PNG y run*<period>.jsonl completo. 7) Configuración & Secretos

Objetivo: centralizar y validar parámetros críticos.
Subtareas
config.toml: plaza/sucursal, ritmos, umbrales DQ, tolerancias, rutas, UA.
.env: secretos si aplican (no parece necesario aquí, pero reservar).
Validación al inicio: faltar algo crítico ⇒ abort con mensaje claro.
Implementación sugerida
load_config_toml ya existe; sumar claves: throttle_min_ms, throttle_max_ms, retry_max, dq_min_cba_coverage, dq_max_zero_prices, outlier_unit_price_limits_por_categoria.
Criterios “listo”
Rutas válidas; umbrales legibles; parámetros efectivamente usados. 8) Pruebas Mínimas y CI

Objetivo: salud de parsers y pipeline.
Subtareas
Unit: precio y promos (HTML fixtures), parse de pack y normalización, DQ checks (inputs sintéticos).
Humo E2E: 3–5 URLs por categoría (o usar dry-run con HTML guardado) y válido price_final>0, unit_price_base>0, CBA>0.
CI: optional GH Actions con lint/tests/build reporte.
Implementación sugerida
tests/unit: test_units_pack_cases, test_price_parse_promos, test_dq_thresholds.
tests/integration: test_pipeline_by_category_minimum.
.github/workflows/ci.yml con matrix simple Python 3.10–3.12.
Criterios “listo”
Tests verdes localmente; flujo CI pasa en rama principal. 9) Entregables

CLI: python -m src.cli run --period YYYY-MM
Exports: exports/series*cba.csv, exports/breakdown*<period>.csv
Reporte: reports/<period>.html
Evidencias y logs: evidence/<period>\_<YYYY-MM-DD>/
Documentación: README sobre correr, actualizar canasta, metodología, límites. 10) Riesgos & Mitigaciones

Bloqueos del sitio: throttling + backoff, y opción dry-run para debug sin red.
Cambios DOM: selectors alternativos en config/selectors.json y validación automática de branch.
Estructuras CSV variadas: validación de schema y coerción con logs de filas descartadas.
Deslizamientos metodológicos: versionado de canasta y registro del impacto en índice. 11) Criterios de Aceptación (producción)

Cobertura cba_flag=si ≥ umbral configurado.
Cero price_final=0 en breakdown final.
DQ ok (o justificado en reporte/log).
Reporte navegable con filtros combinables y ordenamiento.
Reproducibilidad: mismo período + mismos CSV ⇒ mismos resultados (serie y breakdown).

continua con el plan, priorizando siempre lo de mayor impacto. Ademas, simplifica mucho mas el filtrado, hazlo con sentido, ajusta botones, posiciones, etc. Columnas promo y stock no interesan, quitalas. Entiende el proyecto integralmente y diseña el ux/ui con sentido, la columna producto dice lo mismo que item casi, qty base que es? por que tiene decimal? piensa todos esos detalles y continua ajustando.
