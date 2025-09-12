# extract_cards.md — selectores DOM

## Variante con `data-testid`

- Precio promocional: `div.precio-promo > div.precio.semibold` + `span.decimales`.
- Precio regular: `div.precio` + `div.precio_complemento span.decimales`.
- Impuestos: `div.impuestos-nacionales`.
- Bandera de promoción: `promo_flag` se activa si se usa `div.precio-promo`.

## Variante "imetrics"

- Productos listados en `div.producto.item`.
- Nombre y URL: `a[id^='btn_nombre_imetrics_']`.
- Precio base: `input[id^='precio_item_imetrics_']`.
- Precio oferta: `input[id^='precio_oferta_item_imetrics_']` (si existe).
- Marca y SKU: `input[id^='brand_item_imetrics_']` y `input[id^='sku_item_imetrics_']`.
- Stock: `div.btnagregarcarritosinstock_*` con `style='display:none'` indica disponible.
