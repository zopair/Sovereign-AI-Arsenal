import ast
import importlib
import sys
from pathlib import Path
from types import ModuleType


def test_celery_uses_existing_redis_and_restricts_task_payloads_to_json(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/3")
    module = importlib.import_module("backend.core.celery_app")
    module = importlib.reload(module)

    assert module.celery_app.conf.broker_url == "redis://localhost:6379/3"
    assert module.celery_app.conf.result_backend == "redis://localhost:6379/3"
    assert module.celery_app.conf.task_serializer == "json"
    assert module.celery_app.conf.result_serializer == "json"
    assert module.celery_app.conf.accept_content == ["json"]
    assert module.celery_app.conf.task_acks_late is True
    assert module.celery_app.conf.worker_prefetch_multiplier == 1
    assert module.celery_app.conf.task_time_limit == 1800
    assert module.celery_app.conf.task_soft_time_limit == 1700
    assert module.celery_app.conf.result_expires == 86400
    assert module.celery_app.conf.broker_transport_options["visibility_timeout"] == 3600


def test_repository_tasks_are_registered_with_bounded_retries():
    from backend.core.repository_tasks import (
        analyze_repository_task,
        discover_repositories_task,
    )

    assert discover_repositories_task.name == "backend.repository_discovery"
    assert analyze_repository_task.name == "backend.repository_analysis"
    assert discover_repositories_task.max_retries == 3
    assert analyze_repository_task.max_retries == 3


def test_discovery_task_creates_its_engine_inside_the_worker(monkeypatch):
    from backend.core.repository_tasks import discover_repositories_task

    fake_routes = ModuleType("backend.api.routes")
    fake_engine = object()
    fake_routes.get_discovery_engine = lambda: fake_engine

    async def discover(engine, queries, max_repos, auto_analyze):
        return {
            "engine_matches": engine is fake_engine,
            "queries": queries,
            "max_repos": max_repos,
            "auto_analyze": auto_analyze,
        }

    fake_routes.discover_and_analyze_repositories = discover
    monkeypatch.setitem(sys.modules, "backend.api.routes", fake_routes)

    result = discover_repositories_task.run(["agents"], 7, False)

    assert result == {
        "engine_matches": True,
        "queries": ["agents"],
        "max_repos": 7,
        "auto_analyze": False,
    }


def test_analysis_task_delegates_to_the_existing_analysis_pipeline(monkeypatch):
    from backend.core.repository_tasks import analyze_repository_task

    fake_routes = ModuleType("backend.api.routes")

    async def analyze(repo_id, force):
        return {"repository_id": repo_id, "force": force}

    fake_routes.perform_comprehensive_analysis = analyze
    monkeypatch.setitem(sys.modules, "backend.api.routes", fake_routes)

    assert analyze_repository_task.run("repo-123", True) == {
        "repository_id": "repo-123",
        "force": True,
    }


def test_api_routes_enqueue_durable_tasks_and_expose_task_status():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    discovery = ast.unparse(functions["discover_repositories"])
    analysis = ast.unparse(functions["analyze_repository"])
    status = ast.unparse(functions["get_task_status"])

    assert ".apply_async(" in discovery
    assert ".delay(" in analysis
    assert "AsyncResult(" in status
    assert "BackgroundTasks" not in routes_path.read_text(encoding="utf-8")


def test_compose_runs_a_separate_worker_against_the_existing_redis_and_postgres():
    compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "  worker:" in compose
    assert "backend.core.celery_app:celery_app" in compose
    assert "REDIS_URL: redis://redis:6379/0" in compose
    assert "backend_data:/app/backend/data" in compose
    assert "--concurrency=1" in compose


def test_github_token_is_not_left_as_an_unexpanded_yaml_placeholder():
    config = (Path(__file__).resolve().parents[1] / "config.yaml").read_text(
        encoding="utf-8"
    )

    assert "token: \"\"" in config
    assert "${GITHUB_TOKEN}" not in config


def test_vector_store_embedding_writes_are_idempotent_for_task_retries():
    source = (
        Path(__file__).resolve().parents[1] / "database" / "vector_store.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    methods = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    for method_name in ("add_repository_embedding", "batch_add_embeddings"):
        method = ast.unparse(methods[method_name])
        assert "self.collection.upsert(" in method
        assert "self.collection.add(" not in method
