"""Command-line interface for IPC Ushuaia.

Provides three subcommands:

``run``
    Ejecuta el pipeline completo en línea.
``dry-run``
    Usa HTML guardado para depurar selectores y normalización.
``export-series``
    Reexporta CSV/HTML a partir de datos ya persistidos.

All subcommands comparten argumentos comunes como ``--period`` (formato
``YYYY-MM``), ``--branch`` y ``--headless``. Las entradas se validan antes de
ejecutar cualquier operación para evitar errores silenciosos.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Aseguramos que los módulos locales puedan importarse cuando se ejecuta
# ``python ipc-ushuaia/src/cli.py`` directamente.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from exporter import export_series, export_to_html

# ---------------------------------------------------------------------------
# Helpers de validación
# ---------------------------------------------------------------------------

VALID_BRANCHES = {"ushuaia"}


def period_type(value: str) -> str:
    """Valida que ``value`` respete el formato ``YYYY-MM``."""

    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise argparse.ArgumentTypeError("period must be in YYYY-MM format")
    return value


def branch_type(value: str) -> str:
    """Valida que la sucursal esté en la lista soportada."""

    value = value.lower()
    if value not in VALID_BRANCHES:
        raise argparse.ArgumentTypeError(
            f"branch must be one of: {', '.join(sorted(VALID_BRANCHES))}"
        )
    return value


# ---------------------------------------------------------------------------
# Construcción del parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IPC Ushuaia CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Argumentos comunes
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--period",
        type=period_type,
        required=True,
        help="Período a procesar (formato YYYY-MM)",
    )
    common.add_argument(
        "--branch",
        type=branch_type,
        default="ushuaia",
        help="Sucursal de La Anónima",
    )
    common.add_argument(
        "--headless",
        action="store_true",
        help="Ejecutar scraper en modo headless",
    )

    # subcomando: run
    run_parser = subparsers.add_parser(
        "run",
        parents=[common],
        help="Ejecuta pipeline completo en línea",
    )
    run_parser.add_argument(
        "--ae", type=float, default=1.0, help="Multiplicador de Adulto Equivalente"
    )

    # subcomando: dry-run
    dry_parser = subparsers.add_parser(
        "dry-run",
        parents=[common],
        help="Usa HTML guardado para depurar selectores y normalización",
    )
    dry_parser.add_argument(
        "--html-path",
        type=Path,
        help="Ruta al HTML previamente guardado",
    )

    # subcomando: export-series
    export_parser = subparsers.add_parser(
        "export-series",
        parents=[common],
        help="Reexporta CSV/HTML a partir de datos persistidos",
    )
    export_parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "exports"
        / "series_cba.csv",
        help="CSV con la serie histórica",
    )
    export_parser.add_argument(
        "--output",
        type=Path,
        help="Ruta base de exportación (sin extensión)",
    )

    return parser


# ---------------------------------------------------------------------------
# Lógica de los comandos
# ---------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> None:
    print(
        f"Ejecutando pipeline para {args.period} en {args.branch} "
        f"headless={args.headless} AE={args.ae}"
    )
    # TODO: Integrar con el pipeline real.


def _cmd_dry_run(args: argparse.Namespace) -> None:
    print(
        f"Dry-run para {args.period} en {args.branch} headless={args.headless} "
        f"html={args.html_path}"
    )
    # TODO: Integrar con lógica de depuración.


def _cmd_export_series(args: argparse.Namespace) -> None:
    import pandas as pd

    df = pd.read_csv(args.input)
    base: Path = args.output if args.output else args.input.with_suffix("")
    csv_path = export_series(df, str(base) + ".csv")
    export_to_html(df, str(base) + ".html")
    print(f"Serie exportada en {csv_path} y {base}.html")


COMMAND_DISPATCH = {
    "run": _cmd_run,
    "dry-run": _cmd_dry_run,
    "export-series": _cmd_export_series,
}


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMAND_DISPATCH[args.command]
    handler(args)


if __name__ == "__main__":
    main()

