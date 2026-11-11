import os
from pathlib import Path

import yaml
import pytest

from backend.database.url import build_database_url


ROOT = Path(__file__).resolve().parents[2]


def test_database_url_uses_environment_and_escapes_credentials():
    url = build_database_url({
        "DB_HOST": "postgres",
        "DB_PORT": "5432",
        "DB_NAME": "sovereign_ai_arsenal",
        "DB_USER": "app_user",
        "DB_PASSWORD": "p@ss/word",
    }, {})

    assert url.render_as_string(hide_password=False) == (
        "postgresql+psycopg2://app_user:p%40ss%2Fword@postgres:5432/sovereign_ai_arsenal"
    )


def test_database_url_rejects_missing_password():
    with pytest.raises(ValueError, match="DB_PASSWORD"):
        build_database_url({"DB_USER": "app_user"}, {})


def test_compose_does_not_enable_trust_authentication_or_default_passwords():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    postgres = compose["services"]["postgres"]

    assert "POSTGRES_HOST_AUTH_METHOD" not in postgres.get("environment", {})
    assert "${DB_PASSWORD:?DB_PASSWORD must be set}" in postgres["environment"]["POSTGRES_PASSWORD"]
    assert postgres["environment"]["POSTGRES_DB"] == "sovereign_ai_arsenal"


def test_compose_publishes_stateful_admin_ports_only_on_loopback():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

    assert compose["services"]["postgres"]["ports"] == ["127.0.0.1:${POSTGRES_PORT:-5432}:5432"]
    assert "ports" not in compose["services"]["redis"]
    assert compose["services"]["grafana"]["ports"] == ["127.0.0.1:${GRAFANA_PORT:-3000}:3000"]
    assert compose["services"]["prometheus"]["ports"] == ["127.0.0.1:${PROMETHEUS_PORT:-9090}:9090"]

def test_app_config_disables_wildcard_cors_by_default():
    config = yaml.safe_load((ROOT / "backend" / "config.yaml").read_text())
    assert config["api"]["cors_origins"] == []
    assert "*" not in config["api"]["cors_origins"]


def test_app_config_has_no_committed_database_password():
    config = yaml.safe_load((ROOT / "backend" / "config.yaml").read_text())
    assert "password" not in config["database"]
