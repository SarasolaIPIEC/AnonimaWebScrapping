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
- Tarjeta de producto: `[data-testid='product-card']`
- Nombre: `[data-testid='product-name']`
- Precio promocional: `div.precio-promo > div.precio.semibold` + `span.decimales`
- Precio regular: `div.precio` + `div.precio_complemento span.decimales`
- Impuestos: `div.impuestos-nacionales`
- Bandera OOS: `[data-testid='out-of-stock']`
- Sucursal activa: `[data-testid='current-branch']`

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
- Documentar ejemplos de HTML y productos extraídos
## Ejemplo de tarjeta de producto

```html
<div data-testid='product-card'>
  <div data-testid='product-name'>Promo Prod</div>
  <div class='precio-promo'>
    <div class='precio semibold'>$ 1.900</div>
    <div class='precio_complemento'><span class='decimales'>,00</span></div>
  </div>
  <div class='impuestos-nacionales'>IVA 21%</div>
</div>
```

Este HTML fue capturado durante pruebas de parsing y sirve como referencia para
los selectores definitivos.
