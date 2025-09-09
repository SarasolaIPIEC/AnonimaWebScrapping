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

## Validaciones y flags
- Sumar cantidades por rubro y total para control de integridad.
- Verificar consistencia de unidades y prorrateos.
- Marcar ítems sin SKU encontrado para revisión manual.

## Reglas de matching y sustitución
- Matching por nombre, marca, tamaño y categoría usando palabras clave.
- Si hay varias presentaciones, elegir la de menor precio por unidad estándar.
- Documentar toda sustitución o prorrateo en la columna `notes`.
