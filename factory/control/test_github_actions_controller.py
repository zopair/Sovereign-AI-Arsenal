from factory.control.github_actions_controller import (
    FailureClass,
    JobEvidence,
    classify_job,
    decide_recovery,
)


def test_no_steps_is_pre_execution_failure():
    evidence = JobEvidence("failure", steps_present=False, logs_available=False)
    assert classify_job(evidence) == FailureClass.PRE_EXECUTION
    decision = decide_recovery(evidence)
    assert decision.retry_job
    assert decision.alternate_backend
    assert decision.retry_limit == 1


def test_failed_job_with_logs_is_not_misclassified_as_runner_failure():
    evidence = JobEvidence("failure", steps_present=True, logs_available=True)
    decision = decide_recovery(evidence)
    assert decision.classification == FailureClass.TEST
    assert not decision.retry_job
