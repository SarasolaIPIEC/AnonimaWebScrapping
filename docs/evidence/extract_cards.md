# extract_cards.md — selectores DOM

- Precio promocional: `div.precio-promo > div.precio.semibold` + `span.decimales`.
- Precio regular: `div.precio` + `div.precio_complemento span.decimales`.
- Impuestos: `div.impuestos-nacionales`.
- Bandera de promoción: `promo_flag` se activa si se usa `div.precio-promo`.
