from factory.registry.agent_selector import AgentCandidate, rank


def test_rank_excludes_unverified_candidates():
    candidates = [
        AgentCandidate("good", frozenset({"code"}), True, True, True, 8.0),
        AgentCandidate("popular-but-unverified", frozenset({"code"}), True, False, True, 10.0),
    ]
    result = rank(candidates, frozenset({"code"}))
    assert [c.name for c in result] == ["good"]
