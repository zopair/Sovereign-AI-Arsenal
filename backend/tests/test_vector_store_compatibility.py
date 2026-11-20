import ast
from pathlib import Path


def test_vector_store_initialization_uses_chroma_get_or_create_collection():
    source_path = Path(__file__).resolve().parents[1] / "database" / "vector_store.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    initializer = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_initialize"
    )

    calls = [
        node for node in ast.walk(initializer)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    ]
    assert any(call.func.attr == "get_or_create_collection" for call in calls)
    assert not any(
        isinstance(node, ast.Attribute)
        and node.attr == "exceptions"
        and isinstance(node.value, ast.Name)
        and node.value.id == "chromadb"
        for node in ast.walk(initializer)
    )
