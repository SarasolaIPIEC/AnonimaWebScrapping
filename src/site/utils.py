import json
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urljoin

DEFAULT_SITE_BASE = "https://www.laanonima.com.ar/"
LEGACY_BASES = (
    "https://supermercado.laanonimaonline.com/",
    "https://www.laanonimaonline.com/",
)


def json_log(path: str, event: str, payload: Dict[str, Any]) -> None:
    rec = {
        'ts': datetime.utcnow().isoformat() + 'Z',
        'event': event,
        **payload,
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_product_url(
    product_identifier: str,
    slug: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
) -> str:
    """Return an absolute PDP URL for La Anónima.

    ``product_identifier`` can be:
      - an absolute URL (legacy or new) -> it is normalized to the new host
      - a relative path like ``/carne/art_123/`` -> it is joined with ``base_url``
      - an article code ``art_123`` plus ``slug`` -> they are combined
    """

    base = (base_url or DEFAULT_SITE_BASE).rstrip('/') + '/'
    slug = (slug or '').strip().strip('/')
    raw = (product_identifier or '').strip()
    if not raw and not slug:
        raise ValueError("product identifier or slug is required")

    def _rewrite_host(url: str) -> str:
        for legacy in LEGACY_BASES:
            if url.startswith(legacy):
                return base + url[len(legacy):]
        return url

    if raw.startswith("http://") or raw.startswith("https://"):
        normalized = _rewrite_host(raw)
    else:
        path = raw.strip().strip('/')
        if not path and slug:
            path = slug
        elif path.startswith("art_") and slug:
            path = f"{slug}/{path}"
        if not path.startswith("art_") and slug and path and not path.startswith(slug):
            # If only an article code was provided without prefix, append slug
            if path.startswith("art_"):
                path = f"{slug}/{path}"
        if path and "art_" in path and not path.endswith("/"):
            path += "/"
        if path and not path.startswith("/"):
            path = f"/{path}"
        normalized = urljoin(base, path or "/")

    # ensure final slash for PDPs
    if "art_" in normalized and not normalized.endswith("/"):
        normalized += "/"
    return normalized

