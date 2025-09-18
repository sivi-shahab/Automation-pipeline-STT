"""Queue and worker utilities for sending WAV files to the STT API via RabbitMQ."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pika
import requests
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError
from requests import RequestException

from .config import RabbitMQConfig, STTConfig


@dataclass(slots=True)
class STTTask:
    """Representation of a transcription request."""

    ticket_id: str
    wav_path: Path

    def to_payload(self) -> bytes:
        """Serialise the task into a JSON payload."""

        payload = {"ticket_id": self.ticket_id, "wav_path": str(self.wav_path)}
        return json.dumps(payload).encode("utf-8")

    @classmethod
    def from_payload(cls, payload: bytes) -> "STTTask":
        """Reconstruct a task instance from a JSON payload."""

        data = json.loads(payload.decode("utf-8"))
        ticket_id = data["ticket_id"]
        wav_path = Path(data["wav_path"])
        return cls(ticket_id=ticket_id, wav_path=wav_path)


class STTQueue:
    """A RabbitMQ-backed background worker that sends WAV files to the STT API."""

    def __init__(
        self,
        stt_config: STTConfig,
        rabbitmq_config: RabbitMQConfig,
        *,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.stt_config = stt_config
        self.rabbitmq_config = rabbitmq_config
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self._connection_params = self.rabbitmq_config.connection_parameters()
        self._consumer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the queue worker if it is not already running."""

        if self._consumer_thread and self._consumer_thread.is_alive():
            return
        self._ensure_queue()
        self._stop_event.clear()
        self._consumer_thread = threading.Thread(
            target=self._run,
            name="stt-rabbitmq-worker",
            daemon=True,
        )
        self._consumer_thread.start()
        self.logger.info("STT queue worker started")

    def stop(self) -> None:
        """Signal the worker to stop and wait briefly for shutdown."""

        if not self._consumer_thread:
            return
        self._stop_event.set()
        self._consumer_thread.join(timeout=5)
        if self._consumer_thread.is_alive():
            self.logger.warning("STT queue worker did not shut down cleanly")
        else:
            self.logger.info("STT queue worker stopped")
            self._stop_event.clear()
        self._consumer_thread = None

    def enqueue(self, ticket_id: str, wav_path: Path) -> None:
        """Publish a new task to RabbitMQ for processing."""

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
        self._publish_task(task)
        self.logger.debug(
            "Queued STT transcription request for ticket_id=%s at %s",
            ticket_id,
            wav_path,
        )

    def _ensure_queue(self) -> None:
        """Ensure that the RabbitMQ queue exists."""

        connection: Optional[pika.BlockingConnection] = None
        channel: Optional[BlockingChannel] = None
        try:
            connection = pika.BlockingConnection(self._connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=self.rabbitmq_config.queue_name, durable=True)
        finally:
            if channel and channel.is_open:
                channel.close()
            if connection and connection.is_open:
                connection.close()

    def _publish_task(self, task: STTTask) -> None:
        """Publish a task to the RabbitMQ queue with retry handling."""

        payload = task.to_payload()
        attempts = max(1, self.rabbitmq_config.publish_retries)
        for attempt in range(1, attempts + 1):
            connection: Optional[pika.BlockingConnection] = None
            channel: Optional[BlockingChannel] = None
            try:
                connection = pika.BlockingConnection(self._connection_params)
                channel = connection.channel()
                channel.queue_declare(queue=self.rabbitmq_config.queue_name, durable=True)
                channel.basic_publish(
                    exchange="",
                    routing_key=self.rabbitmq_config.queue_name,
                    body=payload,
                    properties=pika.BasicProperties(delivery_mode=2),
                )
                return
            except AMQPConnectionError as exc:
                self.logger.warning(
                    "Failed to publish STT task for ticket_id=%s (attempt %d/%d): %s",
                    task.ticket_id,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(self.rabbitmq_config.reconnect_delay)
            finally:
                if channel and channel.is_open:
                    channel.close()
                if connection and connection.is_open:
                    connection.close()
        raise RuntimeError(
            f"Unable to publish STT task for ticket_id={task.ticket_id} after {attempts} attempts"
        )

    def _run(self) -> None:
        """Worker loop that consumes tasks from RabbitMQ."""

        while not self._stop_event.is_set():
            connection: Optional[pika.BlockingConnection] = None
            channel: Optional[BlockingChannel] = None
            try:
                connection = pika.BlockingConnection(self._connection_params)
                channel = connection.channel()
                self._configure_channel(channel)
                self.logger.info("STT queue worker connected to RabbitMQ")
                self._consume(channel)
            except AMQPConnectionError as exc:
                if self._stop_event.is_set():
                    break
                self.logger.warning(
                    "RabbitMQ connection lost: %s. Retrying in %.1f seconds",
                    exc,
                    self.rabbitmq_config.reconnect_delay,
                )
                time.sleep(self.rabbitmq_config.reconnect_delay)
            except Exception:  # noqa: BLE001
                if self._stop_event.is_set():
                    break
                self.logger.exception("Unexpected error in STT queue worker loop")
                time.sleep(self.rabbitmq_config.reconnect_delay)
            finally:
                if channel and channel.is_open:
                    channel.close()
                if connection and connection.is_open:
                    connection.close()

    def _configure_channel(self, channel: BlockingChannel) -> None:
        """Configure a channel for consumption."""

        channel.queue_declare(queue=self.rabbitmq_config.queue_name, durable=True)
        prefetch = max(1, self.rabbitmq_config.prefetch_count)
        channel.basic_qos(prefetch_count=prefetch)

    def _consume(self, channel: BlockingChannel) -> None:
        """Consume tasks from RabbitMQ until stopped."""

        while not self._stop_event.is_set():
            method_frame, _properties, body = channel.basic_get(
                queue=self.rabbitmq_config.queue_name,
                auto_ack=False,
            )
            if method_frame is None:
                time.sleep(0.5)
                continue
            try:
                task = STTTask.from_payload(body)
            except (KeyError, ValueError, TypeError) as exc:
                self.logger.error("Discarding malformed STT task payload: %s", exc)
                channel.basic_ack(method_frame.delivery_tag)
                continue

            success = False
            try:
                success = self._process_task(task)
            except Exception:  # noqa: BLE001
                self.logger.exception(
                    "Unexpected error while processing STT task for ticket_id=%s",
                    task.ticket_id,
                )

            if success:
                channel.basic_ack(method_frame.delivery_tag)
            else:
                channel.basic_nack(
                    method_frame.delivery_tag,
                    requeue=self.rabbitmq_config.requeue_on_fail,
                )

    def _process_task(self, task: STTTask) -> bool:
        """Attempt to deliver the task to the STT API with retries."""

        if not task.wav_path.exists():
            self.logger.error(
                "STT task for ticket_id=%s failed; file missing at %s",
                task.ticket_id,
                task.wav_path,
            )
            return False

        for attempt in range(1, self.stt_config.max_retries + 1):
            try:
                if self._send_request(task):
                    return True
            except FileNotFoundError:
                self.logger.error(
                    "STT task for ticket_id=%s failed; file missing at %s",
                    task.ticket_id,
                    task.wav_path,
                )
                return False
            except RequestException as exc:
                self.logger.warning(
                    "STT request attempt %d for ticket_id=%s failed: %s",
                    attempt,
                    task.ticket_id,
                    exc,
                )
            if attempt < self.stt_config.max_retries:
                sleep_for = self.stt_config.retry_backoff * attempt
                time.sleep(sleep_for)

        self.logger.error(
            "Exhausted retries for ticket_id=%s after %d attempts",
            task.ticket_id,
            self.stt_config.max_retries,
        )
        return False

    def _send_request(self, task: STTTask) -> bool:
        """Perform the HTTP request to the STT service."""

        headers = self.stt_config.build_headers()
        with task.wav_path.open("rb") as wav_file:
            files = {
                "file": (task.wav_path.name, wav_file, "audio/wav"),
            }
            data = {"ticket_id": task.ticket_id}
            response = self.session.post(
                self.stt_config.api_url,
                headers=headers,
                data=data,
                files=files,
                timeout=self.stt_config.timeout,
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
