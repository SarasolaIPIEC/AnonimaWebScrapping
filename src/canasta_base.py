# Canasta Básica Alimentaria (CBA) – IPC Ushuaia
# Estructura base compatible con cba_catalog.csv y sku_pins.csv

CANASTA_BASE = [
    {"categoria": "Panadería", "item_id": "pan_1kg", "nombre": "Pan fresco", "unidad": "kg", "cantidad_ae": 2.0, "marca": "estandar"},
    {"categoria": "Lácteos", "item_id": "leche_1l", "nombre": "Leche líquida", "unidad": "l", "cantidad_ae": 10.0, "marca": "estandar"},
    {"categoria": "Lácteos", "item_id": "queso_cremoso_1kg", "nombre": "Queso cremoso", "unidad": "kg", "cantidad_ae": 0.8, "marca": "estandar"},
    {"categoria": "Carnes", "item_id": "carne_picada_1kg", "nombre": "Carne picada", "unidad": "kg", "cantidad_ae": 2.0, "marca": "estandar"},
    {"categoria": "Carnes", "item_id": "pollo_1kg", "nombre": "Pollo", "unidad": "kg", "cantidad_ae": 2.0, "marca": "estandar"},
    {"categoria": "Huevos", "item_id": "huevos_docena", "nombre": "Huevo", "unidad": "unit", "cantidad_ae": 12.0, "marca": "estandar"},
    {"categoria": "Verduras", "item_id": "papa_1kg", "nombre": "Papa", "unidad": "kg", "cantidad_ae": 3.0, "marca": "estandar"},
    {"categoria": "Frutas", "item_id": "manzana_1kg", "nombre": "Manzana", "unidad": "kg", "cantidad_ae": 2.0, "marca": "estandar"},
    {"categoria": "Fideos", "item_id": "fideos_1kg", "nombre": "Fideos secos", "unidad": "kg", "cantidad_ae": 1.5, "marca": "estandar"},
    {"categoria": "Arroz", "item_id": "arroz_1kg", "nombre": "Arroz", "unidad": "kg", "cantidad_ae": 2.0, "marca": "estandar"},
    {"categoria": "Legumbres", "item_id": "lentejas_1kg", "nombre": "Lentejas", "unidad": "kg", "cantidad_ae": 1.0, "marca": "estandar"},
    {"categoria": "Azúcar", "item_id": "azucar_1kg", "nombre": "Azúcar", "unidad": "kg", "cantidad_ae": 1.5, "marca": "estandar"},
    {"categoria": "Aceite", "item_id": "aceite_girasol_1_5l", "nombre": "Aceite girasol", "unidad": "l", "cantidad_ae": 1.5, "marca": "estandar"},
    {"categoria": "Otros", "item_id": "sal_fina_500g", "nombre": "Sal fina", "unidad": "kg", "cantidad_ae": 0.5, "marca": "estandar"},
    {"categoria": "Otros", "item_id": "yerba_1kg", "nombre": "Yerba mate", "unidad": "kg", "cantidad_ae": 0.75, "marca": "estandar"},
]

FAMILIA_AE = 3.09

# Utilidad para obtener cantidad por AE y por familia
def get_cantidad(item_id, multiplicador=1.0):
    for item in CANASTA_BASE:
        if item["item_id"] == item_id:
            return item["cantidad_ae"] * multiplicador
    return 0
