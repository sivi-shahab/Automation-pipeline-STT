"""Core ETL pipeline orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .audio_conversion import AudioConversionError, convert_gsm_to_wav
from .config import DatabaseConfig, ETLConfig
from .db import fetch_pending_records, get_connection, mark_records_processed
from .file_system import (
    MissingSourceFileError,
    archive_source_file,
    resolve_file_path,
)

Record = Mapping[str, object]


class ETLPipeline:
    """Encapsulates the GSM to WAV ETL workflow."""

    def __init__(
        self,
        db_config: DatabaseConfig,
        etl_config: ETLConfig,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.db_config = db_config
        self.etl_config = etl_config
        self.logger = logger or logging.getLogger(__name__)

    def run_batch(self) -> None:
        """Process a batch of records as configured."""

        self.logger.info("Starting batch ETL run")
        self.etl_config.ensure_directories()
        with get_connection(self.db_config) as conn:
            records = fetch_pending_records(
                conn, self.etl_config.file_query, self.etl_config.batch_size
            )
            self.logger.info("Fetched %d pending records", len(records))
            processed_ticket_ids = self._process_records(records)
            mark_records_processed(conn, processed_ticket_ids)
            self.logger.info(
                "Batch ETL completed for %d records", len(processed_ticket_ids)
            )

    def process_single(self, ticket_id: str, file_path: str) -> Path:
        """Process a single record, used for near real-time ingestion."""

        record = {"ticket_id": ticket_id, "file_path": file_path}
        self.etl_config.ensure_directories()
        with get_connection(self.db_config) as conn:
            processed = self._process_records([record])
            if not processed:
                raise RuntimeError(
                    f"Processing failed for ticket_id={ticket_id} file_path={file_path}"
                )
            mark_records_processed(conn, processed)
        return self._determine_destination_path(ticket_id)

    def _process_records(self, records: Sequence[Record]) -> Iterable[str]:
        """Process records and yield ticket IDs that completed successfully."""

        successful: list[str] = []
        for record in records:
            ticket_id_raw = record.get("ticket_id")
            file_path_raw = record.get("file_path")
            if not ticket_id_raw or not file_path_raw:
                self.logger.error("Skipping record with incomplete data: %s", record)
                continue

            ticket_id = str(ticket_id_raw)
            file_path = str(file_path_raw)
            try:
                source_path = resolve_file_path(self.etl_config.source_root, file_path)
                destination = self._determine_destination_path(ticket_id)
                convert_gsm_to_wav(
                    source_path,
                    destination,
                    ffmpeg_binary=self.etl_config.ffmpeg_binary,
                )
                archive_source_file(source_path, self.etl_config.archive_root)
                successful.append(ticket_id)
                self.logger.info(
                    "Converted ticket_id=%s from %s to %s",
                    ticket_id,
                    source_path,
                    destination,
                )
            except MissingSourceFileError as exc:
                self.logger.error("Source file missing for ticket_id=%s: %s", ticket_id, exc)
            except AudioConversionError as exc:
                self.logger.error(
                    "Audio conversion failed for ticket_id=%s: %s", ticket_id, exc
                )
            except Exception as exc:  # noqa: BLE001
                self.logger.exception(
                    "Unexpected error while processing ticket_id=%s: %s",
                    ticket_id,
                    exc,
                )
        return successful

    def _determine_destination_path(self, ticket_id: str) -> Path:
        """Compute the destination path for the converted WAV file."""

        filename = f"{ticket_id}.wav"
        return self.etl_config.output_root / filename
