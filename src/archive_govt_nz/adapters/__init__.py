"""Source capture adapters for external services and protocols."""

from __future__ import annotations

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.adapters.bluesky import BlueskyCaptureAdapter
from archive_govt_nz.adapters.email import EmailCaptureAdapter
from archive_govt_nz.adapters.feeds import FeedCaptureAdapter
from archive_govt_nz.adapters.threads import ThreadsCaptureAdapter
from archive_govt_nz.adapters.x_twitter import XCaptureAdapter
from archive_govt_nz.adapters.youtube import YouTubeCaptureAdapter

__all__ = (
    "AdapterCaptureResult",
    "AsyncBaseCaptureAdapter",
    "BlueskyCaptureAdapter",
    "EmailCaptureAdapter",
    "FeedCaptureAdapter",
    "ThreadsCaptureAdapter",
    "XCaptureAdapter",
    "YouTubeCaptureAdapter",
)
