import csv
import glob
import os
from typing import List, Dict, Any


def _read_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return rows
    # try utf-8-sig first, fallback to latin-1 with replacement
    try:
        f = open(path, 'r', encoding='utf-8-sig', newline='')
    except Exception:
        f = open(path, 'r', encoding='utf-8', newline='')
    with f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def read_sku_pins(path: str) -> List[Dict[str, Any]]:
    """Read sku pins file preserving all columns.

    Expected minimal columns: item_id, url, title.
    Optional: brand_tier, cba_flag, category, etc.
    """
    rows = _read_csv(path)
    # normalize keys used by app
    for r in rows:
        r.setdefault('item_id', '')
        r.setdefault('url', '')
        r.setdefault('title', '')
        # optional metadata
        r.setdefault('brand_tier', '')
        r.setdefault('cba_flag', '')
        r.setdefault('category', '')
    return rows


def read_by_category(glob_pattern: str = 'by_category/*.csv') -> List[Dict[str, Any]]:
    """Read per-category CSVs and merge into a unified list.

    Expected columns: period,item_id,url,title,brand_tier,cba_flag,category
    Deduplicate by (period,item_id,url).
    """
    files = sorted(glob.glob(glob_pattern))
    merged: List[Dict[str, Any]] = []
    seen = set()
    for fp in files:
        # tolerate encoding variance across files
        try:
            f = open(fp, 'r', encoding='utf-8-sig', newline='')
        except Exception:
            f = open(fp, 'r', encoding='utf-8', newline='')
        with f:
            reader = csv.DictReader(f)
            for row in reader:
                period = (row.get('period') or '').strip()
                item_id = (row.get('item_id') or '').strip()
                url = (row.get('url') or '').strip()
                key = (period, item_id, url)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(dict(row))
    return merged

