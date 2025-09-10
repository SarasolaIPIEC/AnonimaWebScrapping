# Pruebas

Este directorio contiene pruebas unitarias e integrales.

## Fixtures centralizadas

El paquete [`tests.fixtures`](./fixtures) ofrece utilidades reutilizables:

- `html_fixture(name="sample_products.html")`: devuelve el HTML de un fixture.
- `csv_fixture(name="cba_catalog.csv")`: ruta a un CSV de pruebas.
- `seed_products()`: lista de productos de ejemplo.

Agregar nuevos archivos en `tests/fixtures` permite usarlos desde estas funciones sin repetir rutas.

## Doubles de red y búsqueda

Para aislar las pruebas de servicios externos se emplean test doubles:

- **HTTP**: el paquete [`responses`](https://github.com/getsentry/responses) intercepta llamadas a `requests`. Ver `tests/integration/test_pipeline.py` para un ejemplo de `responses.get` que devuelve HTML fijo.
- **Búsqueda**: `unittest.mock.patch` permite simular resultados de búsqueda o matching. Ver `tests/unit/test_parser.py` para forzar retornos de `match_sku_to_cba`.

### Extender y reutilizar

1. Registrar nuevas URLs HTTP con `responses.get/post` dentro de un decorador `@responses.activate` o un contexto.
2. Para otros componentes, usar `unittest.mock.patch` sobre la ruta completa de la función y definir `return_value` o `side_effect`.
3. Combinar estas técnicas con los helpers de `tests.fixtures` para mantener las pruebas concisas.
