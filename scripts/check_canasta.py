"""Verifica que todos los items de la canasta base aparezcan en el breakdown del periodo."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.canasta_base import CANASTA_BASE


def _load_breakdown(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    with path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        return {row.get('item_id', '').strip(): row for row in reader if row.get('item_id')}


def main() -> int:
    parser = argparse.ArgumentParser(description='Audita la cobertura de la canasta base en un breakdown CSV.')
    parser.add_argument('--period', required=True, help='Periodo YYYY-MM a revisar (ej. 2025-11)')
    parser.add_argument('--breakdown', help='Ruta alternativa a breakdown_<period>.csv')
    args = parser.parse_args()

    period = args.period
    target = Path(args.breakdown or f'exports/breakdown_{period}.csv')

    try:
        breakdown = _load_breakdown(target)
    except Exception as exc:  # pragma: no cover - cli utility
        print(f"[ERROR] {exc}")
        return 1

    missing = []
    without_price = []
    without_url = []
    for entry in CANASTA_BASE:
        iid = entry['item_id']
        row = breakdown.get(iid)
        if not row:
            missing.append(iid)
            continue
        price = row.get('price_final') or row.get('price_final'.upper())
        try:
            price_ok = float(price) > 0 if price not in (None, '') else False
        except Exception:
            price_ok = False
        if not price_ok:
            without_price.append(iid)
        url = (row.get('url') or '').strip()
        if not url:
            without_url.append(iid)

    if not missing and not without_price and not without_url:
        print(f"[OK] Canasta completa en {target}")
        return 0

    if missing:
        print('\nFaltan en breakdown:')
        for iid in missing:
            print(f"  - {iid}")
    if without_price:
        print('\nSin precio válido:')
        for iid in without_price:
            print(f"  - {iid}")
    if without_url:
        print('\nSin URL asociada:')
        for iid in without_url:
            print(f"  - {iid}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
