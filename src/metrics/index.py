import csv
import os
from typing import Dict, Any, List


def _read_series(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _write_series(path: str, rows: List[Dict[str, Any]]):
    fields = ['period','cba_ae','cba_family','idx','mom','yoy','basket_version']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,'') for k in fields})


def _period_minus(period: str, months: int) -> str:
    # period must be YYYY-MM
    y, m = period.split('-')[:2]
    y = int(y)
    m = int(m)
    total = y * 12 + (m - 1) - months
    ny = total // 12
    nm = (total % 12) + 1
    return f"{ny:04d}-{nm:02d}"


def _read_breakdown(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _parse_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        try:
            s = str(v).replace('$','').replace('.', '').replace(',','.')
            return float(s)
        except Exception:
            return 0.0


def update_series(path: str, period: str, cba_ae: float, cba_family: float, *, breakdown_path: str = '', basket_version: str = 'v1') -> Dict[str, Any]:
    rows = _read_series(path)
    rows.sort(key=lambda r: r['period'])

    # determine current basket base (first row with same basket_version)
    base_row = next((r for r in rows if r.get('basket_version','v1') == basket_version), None)
    prev = rows[-1] if rows else None

    # compute idx
    if not rows:
        idx = 100.0
    elif prev and prev.get('basket_version','v1') != basket_version:
        # encadenamiento: I_t(new) = I_{t-1}(old) * (Σ p_t q_new) / (Σ p_{t-1} q_new)
        prev_period = _period_minus(period, 1)
        prev_path = os.path.join(os.path.dirname(path) or 'exports', f'breakdown_{prev_period}.csv')
        prev_rows = _read_breakdown(prev_path)
        curr_rows = _read_breakdown(breakdown_path) if breakdown_path else []
        # q_new de curr_rows, p_t actual implicit en cba_ae; p_{t-1} de prev_rows
        denom = 0.0
        if prev_rows and curr_rows:
            # map qty base (q0) por item del nuevo basket
            q_map = {r.get('item_id'): _parse_float(r.get('monthly_qty_base')) for r in curr_rows}
            for r in prev_rows:
                iid = r.get('item_id')
                if iid in q_map and str(r.get('cba_flag','')).strip().lower() in ('si','true','1','yes'):
                    uprev = _parse_float(r.get('unit_price_base'))
                    denom += uprev * q_map[iid]
        idx_prev = float(prev.get('idx') or 100.0)
        idx = idx_prev * (cba_ae / denom) if denom > 0 else idx_prev
    else:
        base_cba = _parse_float(base_row['cba_ae']) if base_row else cba_ae
        if base_cba == 0:
            base_cba = cba_ae or 1.0
        idx = (cba_ae / base_cba) * 100.0

    # variations from idx
    mom = ''
    if prev and float(prev.get('idx') or 0) > 0:
        mom = f"{(idx/float(prev['idx']) - 1.0)*100.0:.2f}"
    yoy = ''
    target = _period_minus(period, 12)
    prev12 = next((r for r in rows if r['period'] == target), None)
    if prev12 and float(prev12.get('idx') or 0) > 0:
        yoy = f"{(idx/float(prev12['idx']) - 1.0)*100.0:.2f}"

    # upsert
    existing = next((r for r in rows if r['period'] == period), None)
    row = {
        'period': period,
        'cba_ae': f"{cba_ae:.2f}",
        'cba_family': f"{cba_family:.2f}",
        'idx': f"{idx:.2f}",
        'mom': mom,
        'yoy': yoy,
        'basket_version': basket_version,
    }
    if existing:
        existing.update(row)
    else:
        rows.append(row)
    rows.sort(key=lambda r: r['period'])
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    _write_series(path, rows)
    return row
