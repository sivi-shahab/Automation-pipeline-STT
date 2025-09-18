"""Entrypoint for the webhook-based near real-time ETL service."""

from __future__ import annotations

import logging
import os

import uvicorn

from datachain_etl.config import DatabaseConfig, ETLConfig, RabbitMQConfig, STTConfig
from datachain_etl.etl_core import ETLPipeline
from datachain_etl.logging_config import configure_logging
from datachain_etl.stt_queue import STTQueue
from datachain_etl.webhook import create_app


logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    db_config = DatabaseConfig.from_env()
    etl_config = ETLConfig.from_env()
    pipeline = ETLPipeline(db_config, etl_config)

    stt_config = STTConfig.from_env()
    rabbitmq_config = RabbitMQConfig.from_env(require=False)
    stt_queue: STTQueue | None = None
    if stt_config is None:
        logger.warning(
            "STT_API_URL is not configured. STT queue will be disabled for webhook ingestion."
        )
    elif rabbitmq_config is None:
        logger.warning(
            "RabbitMQ is not configured. STT queue will be disabled for webhook ingestion."
        )
    else:
        stt_queue = STTQueue(stt_config, rabbitmq_config)

    app = create_app(pipeline, stt_queue=stt_queue)

    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        if stt_queue is not None:
            stt_queue.stop()


if __name__ == "__main__":
    main()
