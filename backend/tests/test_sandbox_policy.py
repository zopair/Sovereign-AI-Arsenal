import pytest

from backend.core.sandbox_policy import (
    build_container_security_options,
    managed_container_filters,
    require_gvisor_runtime,
    validate_clone_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/acme/project.git",
        "ssh://git@github.com/acme/project.git",
        "https://github.com.evil.example/acme/project.git",
        "https://user:password@github.com/acme/project.git",
        "https://github.com:8443/acme/project.git",
        "https://github.com/acme/project.git?token=secret",
        "https://github.com/acme/../project.git",
        "https://127.0.0.1/acme/project.git",
    ],
)
def test_clone_url_rejects_non_https_ambiguous_or_untrusted_destinations(url):
    assert not validate_clone_url(url, {"github.com"})


def test_clone_url_accepts_only_canonical_github_https_repository_urls():
    assert validate_clone_url("https://github.com/acme/project.git", {"github.com"})
    assert validate_clone_url("https://github.com/acme/project", {"github.com"})


def test_gvisor_security_profile_fails_closed_and_disables_network_by_default():
    options = build_container_security_options(
        {"memory_limit": "512m", "cpu_limit": "1.0"}
    )

    assert options["runtime"] == "runsc"
    assert options["network_disabled"] is True
    assert options["read_only"] is True
    assert options["cap_drop"] == ["ALL"]
    assert options["security_opt"] == ["no-new-privileges"]
    assert options["pids_limit"] == 128
    assert options["user"] == "65532:65532"
    assert "/tmp" in options["tmpfs"]
    assert options["labels"]["com.zopair.component"] == "sandbox"


def test_network_access_requires_explicit_install_policy_opt_in():
    options = build_container_security_options(
        {"allow_network_for_install": True}
    )

    assert options["network_disabled"] is False
    assert options["read_only"] is True
    assert options["cap_drop"] == ["ALL"]


def test_untrusted_execution_cannot_select_the_standard_runc_runtime():
    with pytest.raises(ValueError, match="runsc"):
        build_container_security_options({"runtime": "runc"})


def test_runtime_check_fails_when_gvisor_is_not_installed():
    with pytest.raises(RuntimeError, match="gVisor"):
        require_gvisor_runtime({"runc": {"path": "runc"}})


def test_runtime_check_rejects_attempted_downgrade_even_when_gvisor_exists():
    with pytest.raises(RuntimeError, match="gVisor"):
        require_gvisor_runtime(
            {"runsc": {"path": "runsc"}, "runc": {"path": "runc"}},
            requested_runtime="runc",
        )


def test_runtime_check_accepts_only_configured_gvisor():
    require_gvisor_runtime({"runsc": {"path": "runsc"}})


def test_cleanup_filters_only_containers_owned_by_this_sandbox_manager():
    assert managed_container_filters() == {
        "label": [
            "com.zopair.application=sovereign-ai-arsenal",
            "com.zopair.component=sandbox",
        ]
    }
