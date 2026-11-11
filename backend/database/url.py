"""Safe SQLAlchemy URL construction for environment-driven deployments."""

import os
from typing import Mapping

from sqlalchemy.engine import URL


def build_database_url(
    environ: Mapping[str, str] | None = None,
    config: Mapping[str, object] | None = None,
) -> URL:
    """Build a PostgreSQL URL without string interpolation of credentials."""
    values = os.environ if environ is None else environ
    settings = config or {}

    host = values.get("DB_HOST") or str(settings.get("host") or "localhost")
    port = int(values.get("DB_PORT") or settings.get("port") or 5432)
    database = values.get("DB_NAME") or str(settings.get("name") or "sovereign_ai_arsenal")
    username = values.get("DB_USER") or str(settings.get("user") or "app_user")
    password = values.get("DB_PASSWORD") or str(settings.get("password") or "")

    if not password:
        raise ValueError("DB_PASSWORD must be set; refusing an empty database credential")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
