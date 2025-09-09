"""
Script para poblar basket_items y products desde cba_catalog.csv
"""

import csv
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from repo import insert_product, insert_basket_item

def seed_basket_items(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_id = insert_product(row['item'], None, row['category'])
            insert_basket_item(product_id, row['monthly_qty_value'], row['monthly_qty_unit'], row.get('notes', ''))
# TODO: Ejecutar este script tras migraciones
