"""
CRUD y consultas para el modelo IPC Ushuaia.
"""

try:
    from .engine import get_connection
except ImportError:
    from engine import get_connection

def insert_product(name, brand, category):
    """Inserta un producto y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products (name, brand, category)
                VALUES (%s, %s, %s)
                ON CONFLICT (name, brand) DO UPDATE SET category=EXCLUDED.category
                RETURNING id;
            """, (name, brand, category))
            return cur.fetchone()[0]

def get_product_by_name(name, brand):
    """Consulta producto por nombre y marca."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, brand, category FROM products WHERE name=%s AND brand=%s
            """, (name, brand))
            return cur.fetchone()

def insert_sku(product_id, code, description, pack_size, pack_unit):
    """Inserta un SKU y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO skus (product_id, code, description, pack_size, pack_unit)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET description=EXCLUDED.description, pack_size=EXCLUDED.pack_size, pack_unit=EXCLUDED.pack_unit
                RETURNING id;
            """, (product_id, code, description, pack_size, pack_unit))
            return cur.fetchone()[0]

def insert_price(sku_id, run_id, price_final, promo, stock):
    """Inserta un precio y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO prices (sku_id, run_id, price_final, promo, stock)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (sku_id, run_id) DO UPDATE SET price_final=EXCLUDED.price_final, promo=EXCLUDED.promo, stock=EXCLUDED.stock
                RETURNING id;
            """, (sku_id, run_id, price_final, promo, stock))
            return cur.fetchone()[0]

def insert_basket_item(product_id, monthly_qty_value, monthly_qty_unit, notes):
    """Inserta un ítem de canasta y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO basket_items (product_id, monthly_qty_value, monthly_qty_unit, notes)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (product_id, monthly_qty_value, monthly_qty_unit, notes))
            return cur.fetchone()[0]

def insert_run(run_date, branch, status):
    """Inserta un run y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO runs (run_date, branch, status)
                VALUES (%s, %s, %s)
                ON CONFLICT (run_date, branch) DO UPDATE SET status=EXCLUDED.status
                RETURNING id;
            """, (run_date, branch, status))
            return cur.fetchone()[0]

def insert_index_value(run_id, cba_ae, cba_family, index_value, var_mm, var_ia):
    """Inserta valores de índice y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO index_values (run_id, cba_ae, cba_family, index_value, var_mm, var_ia)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (run_id, cba_ae, cba_family, index_value, var_mm, var_ia))
            return cur.fetchone()[0]

def insert_log(run_id, level, message):
    """Inserta un log y retorna su id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO logs (run_id, level, message)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (run_id, level, message))
            return cur.fetchone()[0]
# TODO: Agregar funciones de consulta, update y delete según necesidad
