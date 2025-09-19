"""Command-line interface for IPC Ushuaia.

Provides three subcommands:

``run``
    Ejecuta el pipeline completo en lÃ­nea.
``dry-run``
    Usa HTML guardado para depurar selectores y normalizaciÃ³n.
``export-series``
    Reexporta CSV/HTML a partir de datos ya persistidos.

All subcommands comparten argumentos comunes como ``--period`` (formato
``YYYY-MM``), ``--branch`` y ``--headless``. Las entradas se validan antes de
ejecutar cualquier operaciÃ³n para evitar errores silenciosos.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional
import subprocess
from datetime import datetime, timezone

# Aseguramos que los mÃ³dulos locales puedan importarse cuando se ejecuta
# ``python ipc-ushuaia/src/cli.py`` directamente.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from exporter import export_series, export_to_html
import pipeline

# ---------------------------------------------------------------------------
# Helpers de validaciÃ³n
# ---------------------------------------------------------------------------

VALID_BRANCHES = {"ushuaia"}


def period_type(value: str) -> str:
    """Valida que ``value`` respete el formato ``YYYY-MM``."""

    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise argparse.ArgumentTypeError("period must be in YYYY-MM format")
    return value


def branch_type(value: str) -> str:
    """Valida que la sucursal estÃ© en la lista soportada."""

    value = value.lower()
    if value not in VALID_BRANCHES:
        raise argparse.ArgumentTypeError(
            f"branch must be one of: {', '.join(sorted(VALID_BRANCHES))}"
        )
    return value


# ---------------------------------------------------------------------------
# ConstrucciÃ³n del parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IPC Ushuaia CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Argumentos comunes
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--period",
        type=period_type,
        required=False,
        help="PerÃ­odo a procesar (formato YYYY-MM)",
    )
    common.add_argument(
        "--branch",
        type=branch_type,
        default="ushuaia",
        help="Sucursal de La AnÃ³nima",
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
        help="Ejecuta pipeline completo en lÃ­nea",
    )
    run_parser.add_argument(
        "--ae", type=float, default=1.0, help="Multiplicador de Adulto Equivalente"
    )

    # subcomando: dry-run
    dry_parser = subparsers.add_parser(
        "dry-run",
        parents=[common],
        help="Usa HTML guardado para depurar selectores y normalizaciÃ³n",
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
        help="CSV con la serie histÃ³rica",
    )
    export_parser.add_argument(
        "--output",
        type=Path,
        help="Ruta base de exportaciÃ³n (sin extensiÃ³n)",
    )

    # subcomando: pins-run (delegado al CLI real en el directorio raíz del repo)
    pins_parser = subparsers.add_parser(
        "pins-run",
        parents=[common],
        help="Ejecuta extracción usando data/sku_pins.csv (delegado)",
    )
    pins_parser.add_argument(
        "--debug",
        action="store_true",
        help="Ver navegador (pasa --debug al CLI real)",
    )

    return parser


# ---------------------------------------------------------------------------
# LÃ³gica de los comandos
# ---------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> None:
    period = args.period or datetime.now(timezone.utc).strftime("%Y-%m")
    summary = pipeline.run(
        period=period,
        branch=args.branch,
        headless=args.headless,
        ae=args.ae,
    )
    print(
        "Resumen: "
        f"encontrados={summary.found} "
        f"oos={summary.oos} "
        f"sustituciones={summary.substitutions} "
        f"variantes={summary.variants} "
        f"fallbacks={summary.fallbacks}"
    )


def _cmd_dry_run(args: argparse.Namespace) -> None:
    period = args.period or datetime.now(timezone.utc).strftime("%Y-%m")
    print(
        f"Dry-run para {period} en {args.branch} headless={args.headless} "
        f"html={args.html_path}"
    )
    # TODO: Integrar con lÃ³gica de depuraciÃ³n.


def _cmd_export_series(args: argparse.Namespace) -> None:
    import pandas as pd

    df = pd.read_csv(args.input)
    base: Path = args.output if args.output else args.input.with_suffix("")
    csv_path = export_series(df, str(base) + ".csv")
    export_to_html(df, str(base) + ".html")
    print(f"Serie exportada en {csv_path} y {base}.html")


def _cmd_pins_run(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parents[2]
    # Sanitizar argumentos: solo valores esperados y sin shell=True
    period = str(args.period or datetime.now(timezone.utc).strftime("%Y-%m"))
    if not re.match(r"^\d{4}-\d{2}$", period):
        print(f"[ERROR] Periodo inválido: {period}")
        sys.exit(2)
    cmd = [
        sys.executable,
        "-m",
        "src.cli",
        "pins-run",
        "--period",
        period,
    ]
    if args.debug:
        cmd.append("--debug")
    print(f"Delegando a CLI real: {' '.join(cmd)}\n(cwd={root})")
    # subprocess.run sin shell=True, argumentos validados
    proc = subprocess.run(cmd, cwd=root)
    if proc.returncode != 0:
        print(f"[WARN] pins-run terminó con código {proc.returncode}")
    sys.exit(proc.returncode)


COMMAND_DISPATCH = {
    "run": _cmd_run,
    "dry-run": _cmd_dry_run,
    "export-series": _cmd_export_series,
    "pins-run": _cmd_pins_run,
}


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMAND_DISPATCH[args.command]
    handler(args)


if __name__ == "__main__":
    main()


