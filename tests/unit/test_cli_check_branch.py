import importlib.util
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[2] / "ipc-ushuaia" / "src" / "cli.py"


def load_cli_module():
    spec = importlib.util.spec_from_file_location("ipc_cli", CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_check_branch_dispatch(monkeypatch):
    cli = load_cli_module()
    parser = cli.build_parser()
    args = parser.parse_args(["check-branch", "--period", "2024-01", "--debug"])

    calls = []

    def fake_run(cmd, cwd):
        calls.append(cmd)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    try:
        cli._cmd_check_branch(args)
    except SystemExit as e:  # _cmd_check_branch llama sys.exit
        assert e.code == 0

    assert calls, "subprocess.run no fue invocado"
    assert calls[0][3] == "check-branch"
    assert "--debug" in calls[0]
