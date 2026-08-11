import json
from pathlib import Path

from factory.runtime.project_workspace import ProjectWorkspace


def test_workspace_is_factory_owned(tmp_path: Path):
    workspace = ProjectWorkspace(tmp_path / "demo", "demo", source="github:example/demo")
    root = workspace.initialize()
    manifest = json.loads((root / "state" / "workspace.json").read_text(encoding="utf-8"))
    assert manifest["project_id"] == "demo"
    assert manifest["execution_dependency"] == "factory"
    assert manifest["source_sync"] == "optional"
    assert (root / "artifacts").is_dir()
    assert (root / "reports").is_dir()
