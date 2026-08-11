from factory.evaluation.acceptance_scenarios import SCENARIOS


def test_acceptance_suite_has_happy_path_and_faults():
    names = {scenario.name for scenario in SCENARIOS}
    assert "happy-path" in names
    assert {"worker-loss", "test-failure", "dependency-failure"}.issubset(names)


def test_faults_have_recovery_actions():
    for scenario in SCENARIOS:
        if scenario.injected_failure:
            assert scenario.expected_recovery
