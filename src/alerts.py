from __future__ import annotations

"""Módulo de generación de alertas automáticas.

Incluye utilidades para:
- Faltantes de más de ``N`` ítems en la CBA.
- Variaciones de precios mayores al ``X%`` por rubro.
- Fallos críticos durante la extracción.

Cada alerta puede despacharse por correo electrónico o mediante un archivo
bandera y, de requerirse, guarda evidencia en ``data/evidence``.
"""

from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Mapping, Any
import json
import os
import smtplib

# Directorio donde se almacenará la evidencia HTML/JSON
evidence_dir = Path(__file__).resolve().parent.parent / "data" / "evidence"
evidence_dir.mkdir(parents=True, exist_ok=True)


def _save_evidence(content: Any, name: str) -> Path:
    """Guarda ``content`` como HTML o JSON en ``data/evidence``.

    Parameters
    ----------
    content:
        Cadena HTML o datos compatibles con JSON.
    name:
        Prefijo del archivo de salida (sin extensión).
    """

    ext = "json" if isinstance(content, (dict, list)) else "html"
    path = evidence_dir / f"{name}.{ext}"
    if ext == "json":
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(str(content), encoding="utf-8")
    return path


def _send_email(subject: str, body: str, to: str) -> None:
    """Envía un correo electrónico simple usando SMTP."""

    host = os.environ.get("SMTP_HOST", "localhost")
    port = int(os.environ.get("SMTP_PORT", "25"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user or "alert@example.com"
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(host, port) as smtp:
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)


def _dispatch(subject: str, body: str, *, email: str | None = None, flag_file: str | Path | None = None) -> None:
    """Envía la alerta por email y/o archivo bandera."""

    if email:
        _send_email(subject, body, email)
    if flag_file:
        Path(flag_file).write_text(body, encoding="utf-8")


def alert_missing_items(
    missing_items: Iterable[str],
    threshold: int,
    *,
    evidence: Any | None = None,
    email: str | None = None,
    flag_file: str | Path | None = None,
) -> bool:
    """Dispara una alerta si faltan más de ``threshold`` ítems.

    Returns ``True`` si se envió la alerta.
    """

    items = list(missing_items)
    if len(items) > threshold:
        path = _save_evidence(evidence, "missing_items") if evidence is not None else None
        body = f"Se detectaron {len(items)} ítems faltantes (umbral {threshold})."
        if path:
            body += f"\nEvidencia: {path}"
        _dispatch("Alerta: faltantes de ítems", body, email=email, flag_file=flag_file)
        return True
    return False


def alert_price_variation(
    variations: Mapping[str, float],
    threshold: float,
    *,
    evidence: Any | None = None,
    email: str | None = None,
    flag_file: str | Path | None = None,
) -> Mapping[str, float] | None:
    """Alerta por variaciones porcentuales superiores al umbral.

    Parameters
    ----------
    variations:
        Mapeo ``rubro -> variación %``.
    threshold:
        Umbral absoluto de variación.

    Returns
    -------
    Dict con los rubros que superaron el umbral o ``None``.
    """

    triggered = {cat: var for cat, var in variations.items() if abs(var) > threshold}
    if triggered:
        path = _save_evidence(evidence or triggered, "price_variation")
        lines = [f"{cat}: {var:.2f}%" for cat, var in triggered.items()]
        body = "Variaciones superiores al umbral:\n" + "\n".join(lines)
        body += f"\nEvidencia: {path}"
        _dispatch("Alerta: variación de precios", body, email=email, flag_file=flag_file)
        return triggered
    return None


def alert_extraction_failure(
    error: Exception | str,
    *,
    evidence: Any | None = None,
    email: str | None = None,
    flag_file: str | Path | None = None,
) -> None:
    """Registra un fallo crítico de extracción y despacha la alerta."""

    path = _save_evidence(evidence, "extraction_failure") if evidence is not None else None
    body = f"Fallo crítico de extracción: {error}"
    if path:
        body += f"\nEvidencia: {path}"
    _dispatch("Alerta: fallo crítico de extracción", body, email=email, flag_file=flag_file)


__all__ = [
    "alert_missing_items",
    "alert_price_variation",
    "alert_extraction_failure",
]
