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


def test_main_protects_api_and_metrics_and_allows_cors_preflight():
    main_path = Path(__file__).resolve().parents[1] / "main.py"
    source = main_path.read_text(encoding="utf-8")

    assert 'request.url.path.startswith("/api/")' in source
    assert 'request.url.path == "/metrics"' in source
    assert 'request.method != "OPTIONS"' in source
    assert '"X-API-Key"' in source
    assert '"API_AUTH_TOKEN"' in source


def test_compose_requires_api_auth_token_before_startup():
    root = Path(__file__).resolve().parents[2]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    example = (root / ".env.example").read_text(encoding="utf-8")

    assert '${API_AUTH_TOKEN:?API_AUTH_TOKEN must be set}' in compose
    assert "API_AUTH_TOKEN=" in example


def test_workers_open_their_own_database_sessions():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))
    worker_names = {
        "discover_and_analyze_repositories",
        "perform_comprehensive_analysis",
    }

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in worker_names:
            calls = [
                item for item in ast.walk(node)
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr == "get_session"
            ]
            assert calls, f"{node.name} must create its own database sessions"


def test_analysis_passes_attribute_based_repository_snapshot_to_discovery():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))
    worker = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "perform_comprehensive_analysis"
    )

    metric_call = next(
        node for node in ast.walk(worker)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "update_repository_metrics"
    )
    assert isinstance(metric_call.args[0], ast.Call)
    assert isinstance(metric_call.args[0].func, ast.Name)
    assert metric_call.args[0].func.id == "SimpleNamespace"


def test_analysis_keeps_one_discovery_client_open_for_metrics_and_readme():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))
    worker = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "perform_comprehensive_analysis"
    )

    client_context = next(
        node for node in ast.walk(worker)
        if isinstance(node, ast.AsyncWith)
        and any(
            isinstance(item.context_expr, ast.Name)
            and item.context_expr.id == "discovery_engine"
            for item in node.items
        )
    )
    called_methods = {
        item.func.attr for item in ast.walk(client_context)
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute)
    }
    assert "update_repository_metrics" in called_methods
    assert "get_repository_readme" in called_methods


def test_metrics_method_does_not_close_a_caller_owned_discovery_session():
    discovery_path = Path(__file__).resolve().parents[1] / "core" / "discovery.py"
    tree = ast.parse(discovery_path.read_text(encoding="utf-8"))
    method = next(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "update_repository_metrics"
    )
    assert not any(isinstance(node, ast.AsyncWith) for node in ast.walk(method))
