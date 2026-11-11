"""Factory-owned project workspace contract.

A project becomes independently operable after intake. Git hosting is an
optional source/sync adapter rather than the execution dependency.
"""
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ProjectWorkspace:
    root: Path
    project_id: str
    source: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def initialize(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "artifacts").mkdir(exist_ok=True)
        (self.root / "reports").mkdir(exist_ok=True)
        (self.root / "state").mkdir(exist_ok=True)
        manifest = {
            "project_id": self.project_id,
            "source": self.source,
            "metadata": self.metadata,
            "execution_dependency": "factory",
            "source_sync": "optional",
        }
        (self.root / "state" / "workspace.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return self.root

    def artifact_path(self, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError("artifact name must be a single filename")
        return self.root / "artifacts" / name
