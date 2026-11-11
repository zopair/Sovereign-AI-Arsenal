import pytest

from factory.verification.release_gate import verify_release


def test_release_requires_all_evidence():
    result = verify_release(tests_passed=True, security_checked=True, provenance_recorded=True)
    assert result.releasable


def test_release_rejects_missing_evidence():
    with pytest.raises(RuntimeError):
        verify_release(tests_passed=True, security_checked=False, provenance_recorded=True)
