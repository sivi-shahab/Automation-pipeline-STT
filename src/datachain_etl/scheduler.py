"""Scheduling utilities for the ETL pipelines."""

from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .etl_core import ETLPipeline

logger = logging.getLogger(__name__)


class BatchETLScheduler:
    """Schedule the batch ETL job to run nightly between 22:00 and 09:00."""

    def __init__(
        self,
        pipeline: ETLPipeline,
        *,
        timezone: str = "Asia/Jakarta",
        scheduler: Optional[BlockingScheduler] = None,
    ) -> None:
        self.pipeline = pipeline
        self.scheduler = scheduler or BlockingScheduler(timezone=timezone)

    def start(self) -> None:
        """Start the blocking scheduler."""

        hours = [22, 23] + list(range(0, 10))
        hour_expr = ",".join(str(hour) for hour in hours)
        trigger = CronTrigger(hour=hour_expr, minute=0)
        self.scheduler.add_job(self.pipeline.run_batch, trigger, id="nightly-batch")
        logger.info(
            "Scheduled batch ETL job for hours=%s timezone=%s",
            hour_expr,
            self.scheduler.timezone,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        """Stop the scheduler."""

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
