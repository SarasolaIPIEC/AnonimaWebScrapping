# Checklist de Cobertura de Pruebas y Validaciones

## Pruebas Unitarias
- [ ] Parsers de precios y promociones (HTML, JSON)
- [ ] Normalización de unidades y cantidades
- [ ] Matching de SKU y categorías
- [ ] Cálculo de CBA por AE y familia
- [ ] Exportación y reporting

## Pruebas Integrales
- [ ] Dry-run con HTML capturado
- [ ] Pipeline completo con datos sintéticos
- [ ] Validación de thresholds y outliers
- [ ] Reintentos automáticos y recuperación de fallos

## Validaciones Críticas
- [ ] coverage >= umbral definido en config.toml
- [ ] price_final > 0 para todos los ítems relevantes
- [ ] registro de OOS y sustituciones documentado
- [ ] logs y evidencia generados correctamente por run

## CI/CD
- [ ] Flujo CI pasa en rama principal y ramas de trabajo
- [ ] Tests automáticos en push/pull request
- [ ] Lint automático en código Python

**Actualiza este checklist tras cada mejora o PR relevante.**