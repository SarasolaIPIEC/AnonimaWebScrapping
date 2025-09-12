import json
from datetime import datetime
from typing import Dict, Any


def json_log(path: str, event: str, payload: Dict[str, Any]) -> None:
    rec = {
        'ts': datetime.utcnow().isoformat() + 'Z',
        'event': event,
        **payload,
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

