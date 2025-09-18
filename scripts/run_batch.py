"""Entrypoint for the nightly batch ETL scheduler."""

from __future__ import annotations

from datachain_etl.config import DatabaseConfig, ETLConfig
from datachain_etl.etl_core import ETLPipeline
from datachain_etl.logging_config import configure_logging
from datachain_etl.scheduler import BatchETLScheduler


def main() -> None:
    configure_logging()
    db_config = DatabaseConfig.from_env()
    etl_config = ETLConfig.from_env()
    pipeline = ETLPipeline(db_config, etl_config)
    scheduler = BatchETLScheduler(pipeline)
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
