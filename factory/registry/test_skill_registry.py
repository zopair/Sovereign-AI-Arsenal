import pytest

from factory.registry.skill_registry import Skill, SkillRegistry


def test_registry_only_resolves_verified_enabled_skills():
    registry = SkillRegistry()
    registry.register(Skill("android", frozenset({"build", "android"}), source="open-source"))
    assert registry.resolve(frozenset({"android"})) == []
    registry.promote("android", {"tests_passed": True, "security_checked": True})
    assert registry.resolve(frozenset({"android"}))[0].name == "android"


def test_promotion_rejects_missing_security_evidence():
    registry = SkillRegistry()
    registry.register(Skill("unsafe", frozenset({"build"})))
    with pytest.raises(ValueError):
        registry.promote("unsafe", {"tests_passed": True, "security_checked": False})
