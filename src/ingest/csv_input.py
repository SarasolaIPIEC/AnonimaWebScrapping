from pathlib import Path
import csv
import glob
import os
from typing import List, Dict, Any, Iterable, Optional


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



def read_by_category(patterns: Optional[Iterable[str]] = None, expected_period: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read per-category CSVs and merge into a unified list.

    Expected columns: period,item_id,url,title,brand_tier,cba_flag,category
    Deduplicate by (period,item_id,url).
    When a CSV lacks ``period`` it can be filled via ``expected_period``; ``category``
    defaults to the filename stem (title-cased) when missing.
    """
    patterns = list(patterns or ['by_category/*.csv'])
    files: List[str] = []
    for pattern in patterns:
        files.extend(sorted(glob.glob(pattern)))
    merged: List[Dict[str, Any]] = []
    seen = set()
    skip_names = {'sku_pins', 'cba_catalog', 'storage_state'}
    display_map = {
        'higiene y perfumeria': 'Higiene y perfumería',
        'limpieza y hogar': 'Limpieza y hogar',
    }
    for fp in files:
        name = Path(fp).stem.lower()
        if name in skip_names:
            continue
        try:
            f = open(fp, 'r', encoding='utf-8-sig', newline='')
        except Exception:
            f = open(fp, 'r', encoding='utf-8', newline='')
        with f:
            reader = csv.DictReader(f)
            for row in reader:
                period = (row.get('period') or '').strip()
                if not period and expected_period:
                    period = expected_period
                    row['period'] = period
                item_id = (row.get('item_id') or '').strip()
                url = (row.get('url') or '').strip()
                if not item_id or not url:
                    continue
                category = (row.get('category') or '').strip()
                if not category:
                    raw_label = Path(fp).stem.replace('_', ' ').replace('-', ' ').strip()
                    if name in display_map:
                        category = display_map[name]
                    else:
                        words = []
                        for token in raw_label.split():
                            lower = token.lower()
                            if lower in {'y', 'e', 'de', 'del'}:
                                words.append(lower)
                            else:
                                words.append(lower.capitalize())
                        category = ' '.join(words) or raw_label
                    row['category'] = category
                key = (period, item_id, url)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(dict(row))
    return merged



