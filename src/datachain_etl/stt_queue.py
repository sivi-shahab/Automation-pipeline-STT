"""Queue and worker utilities for sending WAV files to the STT API."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from requests import RequestException

from .config import STTConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class STTTask:
    """Representation of a transcription request."""

    ticket_id: str
    wav_path: Path


class STTQueue:
    """A background worker that sends WAV files to the STT API."""

    def __init__(
        self,
        config: STTConfig,
        *,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self._queue: queue.Queue[STTTask | None] = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the queue worker if it is not already running."""

        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._run,
            name="stt-queue-worker",
            daemon=True,
        )
        self._worker.start()
        self.logger.info("STT queue worker started")

    def stop(self) -> None:
        """Signal the worker to stop and wait briefly for shutdown."""

        if not self._worker:
            return
        self._stop_event.set()
        self._queue.put(None)
        self._worker.join(timeout=5)
        self._worker = None
        self.logger.info("STT queue worker stopped")

    def enqueue(self, ticket_id: str, wav_path: Path) -> None:
        """Add a new task to the queue for processing."""

        if not isinstance(wav_path, Path):
            wav_path = Path(wav_path)
        if not wav_path.exists():
            self.logger.error(
                "Cannot enqueue STT task for ticket_id=%s; file missing at %s",
                ticket_id,
                wav_path,
            )
            return
        self.start()
        task = STTTask(ticket_id=ticket_id, wav_path=wav_path)
        self._queue.put(task)
        self.logger.debug(
            "Queued STT transcription request for ticket_id=%s at %s",
            ticket_id,
            wav_path,
        )

    def _run(self) -> None:
        """Worker loop that consumes tasks from the queue."""

        while not self._stop_event.is_set():
            try:
                task = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if task is None:
                self._queue.task_done()
                break

            try:
                self._process_task(task)
            except Exception:  # noqa: BLE001
                self.logger.exception(
                    "Unexpected error while processing STT task for ticket_id=%s",
                    task.ticket_id,
                )
            finally:
                self._queue.task_done()

    def _process_task(self, task: STTTask) -> None:
        """Attempt to deliver the task to the STT API with retries."""

        for attempt in range(1, self.config.max_retries + 1):
            try:
                if self._send_request(task):
                    return
            except FileNotFoundError:
                self.logger.error(
                    "STT task for ticket_id=%s failed; file missing at %s",
                    task.ticket_id,
                    task.wav_path,
                )
                return
            except RequestException as exc:
                self.logger.warning(
                    "STT request attempt %d for ticket_id=%s failed: %s",
                    attempt,
                    task.ticket_id,
                    exc,
                )
            if attempt < self.config.max_retries:
                sleep_for = self.config.retry_backoff * attempt
                time.sleep(sleep_for)
        self.logger.error(
            "Exhausted retries for ticket_id=%s after %d attempts",
            task.ticket_id,
            self.config.max_retries,
        )

    def _send_request(self, task: STTTask) -> bool:
        """Perform the HTTP request to the STT service."""

        headers = self.config.build_headers()
        with task.wav_path.open("rb") as wav_file:
            files = {
                "file": (task.wav_path.name, wav_file, "audio/wav"),
            }
            data = {"ticket_id": task.ticket_id}
            response = self.session.post(
                self.config.api_url,
                headers=headers,
                data=data,
                files=files,
                timeout=self.config.timeout,
            )
        if response.ok:
            self.logger.info(
                "STT request for ticket_id=%s accepted with status %s",
                task.ticket_id,
                response.status_code,
            )
            return True
        self.logger.error(
            "STT API returned status %s for ticket_id=%s: %s",
            response.status_code,
            task.ticket_id,
            response.text,
        )
        return False
