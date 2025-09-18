"""Configuration models for the Datachain ETL service."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

import pika

DEFAULT_FILE_QUERY = (
    """
    SELECT ticket_id, file_path
    FROM audio_jobs
    WHERE processed_at IS NULL
    ORDER BY created_at
    LIMIT %(batch_size)s
    """
    .strip()
)


@dataclass(slots=True)
class DatabaseConfig:
    """Connection details for the Postgres database."""

    host: str
    port: int
    dbname: str
    user: str
    password: str
    connect_timeout: int = 10

    @classmethod
    def from_env(cls, prefix: str = "POSTGRES_") -> "DatabaseConfig":
        """Instantiate the configuration from environment variables.

        Expected environment variables include ``{prefix}HOST``, ``{prefix}PORT``,
        ``{prefix}DBNAME``, ``{prefix}USER`` and ``{prefix}PASSWORD``.
        """

        port_str = os.getenv(f"{prefix}PORT", "5432")
        port = int(port_str)
        missing = [
            key
            for key in ("HOST", "DBNAME", "USER", "PASSWORD")
            if not os.getenv(f"{prefix}{key}")
        ]
        if missing:
            raise RuntimeError(
                "Missing required database environment variables: "
                + ", ".join(f"{prefix}{key}" for key in missing)
            )
        return cls(
            host=os.environ[f"{prefix}HOST"],
            port=port,
            dbname=os.environ[f"{prefix}DBNAME"],
            user=os.environ[f"{prefix}USER"],
            password=os.environ[f"{prefix}PASSWORD"],
        )


@dataclass(slots=True)
class ETLConfig:
    """Runtime configuration for the ETL pipeline."""

    source_root: Path
    output_root: Path
    batch_size: int = 500
    ffmpeg_binary: str = "ffmpeg"
    file_query: str = DEFAULT_FILE_QUERY
    archive_root: Optional[Path] = None

    @classmethod
    def from_env(cls, prefix: str = "ETL_") -> "ETLConfig":
        """Instantiate the ETL configuration from environment variables."""

        source_root = os.getenv(f"{prefix}SOURCE_ROOT")
        output_root = os.getenv(f"{prefix}OUTPUT_ROOT")
        if not source_root or not output_root:
            raise RuntimeError(
                "Both ETL_SOURCE_ROOT and ETL_OUTPUT_ROOT environment variables must be set."
            )
        archive_root = os.getenv(f"{prefix}ARCHIVE_ROOT")
        batch_size = int(os.getenv(f"{prefix}BATCH_SIZE", "500"))
        ffmpeg_binary = os.getenv(f"{prefix}FFMPEG_BINARY", "ffmpeg")
        file_query = os.getenv(f"{prefix}FILE_QUERY", DEFAULT_FILE_QUERY)
        return cls(
            source_root=Path(source_root),
            output_root=Path(output_root),
            batch_size=batch_size,
            ffmpeg_binary=ffmpeg_binary,
            file_query=file_query,
            archive_root=Path(archive_root) if archive_root else None,
        )

    def ensure_directories(self) -> None:
        """Create the directories used by the ETL process if needed."""

        self.source_root.mkdir(parents=True, exist_ok=True)
        self.output_root.mkdir(parents=True, exist_ok=True)
        if self.archive_root:
            self.archive_root.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class STTConfig:
    """Configuration for communicating with the STT API service."""

    api_url: str
    api_key: Optional[str] = None
    api_key_header: str = "Authorization"
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 2.0

    @classmethod
    def from_env(
        cls,
        prefix: str = "STT_",
        *,
        require: bool = False,
    ) -> Optional["STTConfig"]:
        """Instantiate the STT configuration from environment variables."""

        api_url = os.getenv(f"{prefix}API_URL")
        if not api_url:
            if require:
                raise RuntimeError("STT_API_URL environment variable must be provided")
            return None

        api_key = os.getenv(f"{prefix}API_KEY")
        api_key_header = os.getenv(f"{prefix}API_KEY_HEADER", "Authorization")
        timeout = int(os.getenv(f"{prefix}TIMEOUT", "30"))
        max_retries = int(os.getenv(f"{prefix}MAX_RETRIES", "3"))
        retry_backoff = float(os.getenv(f"{prefix}RETRY_BACKOFF", "2.0"))

        return cls(
            api_url=api_url,
            api_key=api_key,
            api_key_header=api_key_header,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )

    def build_headers(self) -> dict[str, str]:
        """Construct request headers for STT API calls."""

        headers: dict[str, str] = {}
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        return headers


@dataclass(slots=True)
class RabbitMQConfig:
    """Connection information for RabbitMQ used by the STT queue."""

    host: str
    port: int = 5672
    username: Optional[str] = None
    password: Optional[str] = None
    virtual_host: str = "/"
    queue_name: str = "stt_tasks"
    prefetch_count: int = 1
    reconnect_delay: float = 5.0
    requeue_on_fail: bool = False
    publish_retries: int = 3

    @classmethod
    def from_env(
        cls,
        prefix: str = "RABBITMQ_",
        *,
        require: bool = True,
    ) -> Optional["RabbitMQConfig"]:
        """Instantiate the RabbitMQ configuration from environment variables."""

        host = os.getenv(f"{prefix}HOST")
        if not host:
            if require:
                raise RuntimeError("RABBITMQ_HOST environment variable must be provided")
            return None

        port = int(os.getenv(f"{prefix}PORT", "5672"))
        username = os.getenv(f"{prefix}USERNAME")
        password = os.getenv(f"{prefix}PASSWORD")
        virtual_host = os.getenv(f"{prefix}VHOST", "/")
        queue_name = os.getenv(f"{prefix}QUEUE", "stt_tasks")
        prefetch_count = int(os.getenv(f"{prefix}PREFETCH_COUNT", "1"))
        reconnect_delay = float(os.getenv(f"{prefix}RECONNECT_DELAY", "5.0"))
        publish_retries = int(os.getenv(f"{prefix}PUBLISH_RETRIES", "3"))
        requeue_on_fail = os.getenv(f"{prefix}REQUEUE_ON_FAIL", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            virtual_host=virtual_host,
            queue_name=queue_name,
            prefetch_count=prefetch_count,
            reconnect_delay=reconnect_delay,
            requeue_on_fail=requeue_on_fail,
            publish_retries=publish_retries,
        )

    def connection_parameters(self) -> pika.ConnectionParameters:
        """Construct a pika connection parameter object."""

        credentials = None
        if self.username:
            credentials = pika.PlainCredentials(self.username, self.password or "")
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=credentials,
        )
