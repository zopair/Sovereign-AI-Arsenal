"""Safe skill registry: skills are discovered and scored before activation."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    name: str
    capabilities: frozenset[str]
    tools: tuple[str, ...] = ()
    source: str = "local"
    trust: str = "unverified"
    enabled: bool = False


@dataclass
class SkillRegistry:
    skills: dict[str, Skill] = field(default_factory=dict)

    def register(self, skill: Skill) -> None:
        if not skill.name.strip():
            raise ValueError("skill name is required")
        self.skills[skill.name] = skill

    def resolve(self, required: frozenset[str]) -> list[Skill]:
        return sorted(
            (s for s in self.skills.values() if s.enabled and required.issubset(s.capabilities) and s.trust == "verified"),
            key=lambda s: (-len(s.capabilities), s.name),
        )

    def promote(self, name: str, evidence: dict) -> Skill:
        skill = self.skills[name]
        if not evidence.get("tests_passed") or not evidence.get("security_checked"):
            raise ValueError("skill requires passing tests and security evidence")
        promoted = Skill(skill.name, skill.capabilities, skill.tools, skill.source, "verified", True)
        self.skills[name] = promoted
        return promoted
