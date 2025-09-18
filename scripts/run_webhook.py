"""Entrypoint for the webhook-based near real-time ETL service."""

from __future__ import annotations

import os

import uvicorn

from datachain_etl.config import DatabaseConfig, ETLConfig
from datachain_etl.etl_core import ETLPipeline
from datachain_etl.logging_config import configure_logging
from datachain_etl.webhook import create_app


def main() -> None:
    configure_logging()
    db_config = DatabaseConfig.from_env()
    etl_config = ETLConfig.from_env()
    pipeline = ETLPipeline(db_config, etl_config)
    app = create_app(pipeline)

    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
