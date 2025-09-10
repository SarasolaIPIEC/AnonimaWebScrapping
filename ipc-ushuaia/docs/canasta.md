# Canasta Básica Alimentaria (CBA) – IPC Ushuaia

## Criterios de representatividad
- Basada en la CBA oficial, adaptada a consumos locales y disponibilidad en La Anónima Ushuaia.
- Selección de ítems representativos y de consumo habitual.
- Cantidades mensuales ajustables por Adulto Equivalente (AE) y multiplicador para familias.
- Documentación de prorrateos, sustituciones y supuestos.

## Decisiones abiertas
- Si no existe SKU exacto, se permite sustitución documentada (ver columna `notes` en cba_catalog.csv).
- Preferencia por presentaciones estándar y marcas de mayor consumo local.
- Prorrateo de ítems de bajo consumo (sal, té) para reflejar gasto mensual.
- Las cantidades pueden ajustarse según metodología vigente o cambios en la CBA oficial.

## Ejemplo de ajuste por AE y familia
- Para familia tipo (3,09 AE), multiplicar cada cantidad mensual por 3,09.
- El sistema debe permitir modificar el multiplicador y las cantidades base.

## Detalle de ítems y cantidades

| Categoría | Ítem | Cantidad AE (unidad) | Cantidad hogar 3,09 AE (unidad) |
|-----------|------|---------------------|---------------------------------|
| Panadería | Pan fresco | 6 kg | 18.54 kg |
| Lácteos | Leche líquida | 9 l | 27.81 l |
| Carnes | Carne vacuna | 5 kg | 15.45 kg |
| Carnes | Pollo | 2 kg | 6.18 kg |
| Huevos | Huevo | 30 unidad | 92.70 unidad |
| Verduras | Papa | 4 kg | 12.36 kg |
| Verduras | Tomate | 2 kg | 6.18 kg |
| Frutas | Manzana | 3 kg | 9.27 kg |
| Fideos | Fideos secos | 2 kg | 6.18 kg |
| Arroz | Arroz | 2 kg | 6.18 kg |
| Legumbres | Lentejas | 1 kg | 3.09 kg |
| Azúcar | Azúcar | 1 kg | 3.09 kg |
| Aceite | Aceite mezcla/girasol | 1.5 l | 4.63 l |
| Otros | Sal fina | 0.2 kg | 0.62 kg |
| Otros | Té | 0.1 kg | 0.31 kg |
| Otros | Yerba mate | 1 kg | 3.09 kg |

## Validaciones y flags
- Sumar cantidades por rubro y total para control de integridad.
- Verificar consistencia de unidades y prorrateos.
- Marcar ítems sin SKU encontrado para revisión manual.

## Reglas de matching y sustitución
- Matching por nombre, marca, tamaño y categoría usando palabras clave.
- Si hay varias presentaciones, elegir la de menor precio por unidad estándar.
- Documentar toda sustitución o prorrateo en la columna `notes`.
