"""Structural regression guard for route-module names used by endpoint bodies.

This test deliberately avoids importing the full API stack so it remains cheap
and does not require optional vector-store/ML packages.
"""
import ast
from pathlib import Path


def test_statistics_route_has_module_level_timedelta_import():
    routes_path = Path(__file__).resolve().parents[1] / "api" / "routes.py"
    tree = ast.parse(routes_path.read_text(encoding="utf-8"))

    imported_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "datetime"
        for alias in node.names
    }

    statistics = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "get_statistics"
    )
    referenced_names = {
        node.id for node in ast.walk(statistics)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }

    assert "timedelta" in referenced_names
    assert "timedelta" in imported_names
