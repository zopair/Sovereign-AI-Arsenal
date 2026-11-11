import ast
from pathlib import Path

from backend.security import api_key_is_valid


def test_api_key_validation_accepts_only_matching_nonempty_keys():
    assert api_key_is_valid("correct-key", "correct-key")
    assert not api_key_is_valid("wrong-key", "correct-key")
    assert not api_key_is_valid("", "correct-key")
    assert not api_key_is_valid("provided-key", "")
    assert not api_key_is_valid(None, "correct-key")


def test_background_workers_do_not_accept_request_scoped_sessions():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))

    worker_names = {
        "discover_and_analyze_repositories",
        "perform_comprehensive_analysis",
    }
    workers = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in worker_names
    }

    assert set(workers) == worker_names
    for worker in workers.values():
        argument_names = {arg.arg for arg in worker.args.args + worker.args.kwonlyargs}
        assert "db" not in argument_names
        assert "session" not in argument_names


def test_request_handlers_do_not_pass_request_session_to_background_workers():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_task":
            continue
        for argument in node.args[1:]:
            assert not (
                isinstance(argument, ast.Name)
                and argument.id in {"db", "session"}
            )
