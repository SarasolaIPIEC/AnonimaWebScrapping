import os
import subprocess
from pathlib import Path

CLI_PATH = Path(__file__).resolve().parents[2] / "ipc-ushuaia" / "src" / "cli.py"


def run_cli(scenario: str) -> str:
    env = os.environ.copy()
    env["TEST_SCENARIO"] = scenario
    cmd = ["python", str(CLI_PATH), "run", "--period", "2024-01"]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
    return result.stdout.strip()


def test_run_nominal():
    out = run_cli("nominal")
    assert "encontrados=3" in out
    assert "oos=0" in out
    assert "sustituciones=0" in out


def test_run_oos():
    out = run_cli("oos")
    assert "oos=1" in out
    assert "sustituciones=1" in out


def test_run_variants():
    out = run_cli("variants")
    assert "variantes=2" in out


def test_run_dom_changed():
    out = run_cli("dom_changed")
    assert "fallbacks=1" in out
