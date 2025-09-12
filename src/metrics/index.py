import csv
import os
from typing import Dict, Any


def _read_series(path: str):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _write_series(path: str, rows):
    fields = ['period','cba_ae','cba_family','idx','mom','yoy']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def update_series(path: str, period: str, cba_ae: float, cba_family: float) -> Dict[str, Any]:
    rows = _read_series(path)
    # ensure sorted by period asc
    rows.sort(key=lambda r: r['period'])

    # find base and previous/current positions
    base_cba = float(rows[0]['cba_ae']) if rows else cba_ae
    if base_cba == 0:
        base_cba = cba_ae or 1.0
    prev = rows[-1] if rows else None

    idx = 100.0 if not rows or base_cba == 0 else (cba_ae / base_cba) * 100.0
    mom = ''
    if prev and float(prev['cba_ae']) > 0:
        mom = f"{(cba_ae/float(prev['cba_ae']) - 1.0)*100.0:.2f}"

    # yoy: find 12 months prior
    yoy = ''
    target = _period_minus(period, 12)
    prev12 = next((r for r in rows if r['period'] == target), None)
    if prev12 and float(prev12['cba_ae']) > 0:
        yoy = f"{(cba_ae/float(prev12['cba_ae']) - 1.0)*100.0:.2f}"

    # upsert current period
    existing = next((r for r in rows if r['period'] == period), None)
    row = {
        'period': period,
        'cba_ae': f"{cba_ae:.2f}",
        'cba_family': f"{cba_family:.2f}",
        'idx': f"{idx:.2f}",
        'mom': mom,
        'yoy': yoy,
    }
    if existing:
        existing.update(row)
    else:
        rows.append(row)
    rows.sort(key=lambda r: r['period'])
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    _write_series(path, rows)
    return row


def _period_minus(period: str, months: int) -> str:
    y, m = period.split('-')
    y = int(y)
    m = int(m)
    total = y * 12 + (m - 1) - months
    ny = total // 12
    nm = (total % 12) + 1
    return f"{ny:04d}-{nm:02d}"
