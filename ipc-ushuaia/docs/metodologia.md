# Metodología IPC Ushuaia

## Canasta y cantidades
La canasta básica alimentaria (CBA) se define por ítems y cantidades mensuales por Adulto Equivalente (AE=1).  El listado completo y su escala a un hogar tipo de 3,09 AE se detalla en [canasta.md](canasta.md).

## Fuentes de precios
- **Origen**: precios finales al consumidor publicados en La Anónima Online, sucursal Ushuaia.
- **Promociones**: si la promoción exhibe un precio efectivo, se toma dicho valor.
- **Cobertura**: se prioriza disponibilidad local; ítems sin stock quedan marcados para revisión.

## Criterios de sustitución
- Cuando un SKU no está disponible, se busca una alternativa de igual categoría y presentación similar.
- Se privilegia el menor precio por unidad estándar entre las opciones disponibles.
- Cada sustitución o prorrateo se documenta en la columna `notes` del archivo `cba_catalog.csv`.

## Limitaciones
- Cambios en la estructura del sitio o en el DOM pueden requerir ajustes en el scraper.
- Las promociones y el stock varían, afectando la representatividad puntual de algunos precios.
- Algunas presentaciones tienen múltiplos o unidades que requieren prorrateo manual.

## Control de cambios
- Todas las modificaciones al catálogo, código y metodología se registran en control de versiones.
- El archivo `cba_catalog.csv` mantiene notas sobre sustituciones y ajustes de cantidades.
- Cada actualización debe incluir comentarios que expliquen el motivo del cambio.

## Diccionario de datos de exportaciones

### Serie histórica (`series_cba.csv`)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `period` | texto | Período de referencia |
| `cba_ae` | numérico | Costo de la canasta por AE |
| `cba_family` | numérico | Costo de la canasta para hogar tipo (3,09 AE) |
| `idx` | numérico | Índice base 100 en el primer período |
| `mom` | numérico | Variación porcentual m/m |
| `yoy` | numérico | Variación porcentual i.a. |

### Desglose por período (`breakdown_<period>.csv`)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `category` | texto | Rubro del ítem |
| `item` | texto | Ítem de la canasta |
| `cost` | numérico | Costo del ítem en el período seleccionado |
