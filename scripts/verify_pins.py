"""Valida que las URLs de data/sku_pins.csv respondan 200."""
from __future__ import annotations

import csv
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT / 'data' / 'sku_pins.csv'

@dataclass
class Result:
    item_id: str
    url: str
    status: int | None
    error: str | None = None


def _check(url: str, timeout: float = 5.0) -> Result:
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'ipc-ushuaia/url-checker'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - trusted domain
            return Result(item_id='', url=url, status=resp.status, error=None)
    except Exception as exc:  # pragma: no cover - network dependent
        return Result(item_id='', url=url, status=None, error=str(exc))


def main() -> int:
    target = DEFAULT_FILE
    if not target.exists():
        print(f"[ERROR] No existe {target}")
        return 1
    rows: List[Result] = []
    with target.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = (row.get('item_id') or '').strip()
            url = (row.get('url') or '').strip()
            if not item_id or not url:
                continue
            result = _check(url)
            result.item_id = item_id
            rows.append(result)
            time.sleep(0.2)
    broken = [r for r in rows if r.status != 200]
    if not rows:
        print('[WARN] No se encontraron URLs en sku_pins')
        return 0
    if broken:
        print('[FAIL] Algunas URLs no responden 200:')
        for r in broken:
            print(f"  - {r.item_id}: {r.url} ({r.status or 'error'}) {r.error or ''}")
        return 1
    print('[OK] Todas las URLs de sku_pins respondieron 200')
    return 0


if __name__ == '__main__':
    sys.exit(main())
