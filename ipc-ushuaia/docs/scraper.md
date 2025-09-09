# Scraper La Anónima Online – Ushuaia

## Contrato de salida de producto

```python
{
    "sku": str,
    "name": str,
    "brand": str,
    "unit": str,
    "pack_size": float,
    "price_final": float,
    "promo": str,
    "stock": bool,
    "category": str,
    "raw_html": str  # para debugging
}
```

## Selectores sugeridos
- Título: `.product-title` o similar
- Unidad: `.product-unit`
- Precio final: `.product-price-final`
- Stock: `.product-stock` o flag OOS
- Promoción: `.product-promo`

## Ejemplo de flujo
1. Lanzar navegador (browser.py)
2. Seleccionar sucursal Ushuaia (branch.py)
3. Buscar o navegar por categoría (search.py)
4. Paginado/scroll y guardar HTML
5. Extraer y normalizar productos (extract.py)
6. Guardar resultados y HTML para pruebas

## Pruebas manuales sugeridas
- Ítem único
- Variantes/promociones
- Producto fuera de stock (OOS)

## TODOs
- Completar selectores reales tras inspección de la web
- Documentar ejemplos de HTML y productos extraídos
