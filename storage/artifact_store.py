"""Artifact persistence for the spec-driven-framework.

Artifacts (spec.md, solution files, test_results.txt, audit_report.txt) are
written to the local working directory and optionally uploaded to S3.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from config import settings

logger = logging.getLogger(__name__)

# Map file extensions to the correct Content-Type for S3 uploads.
_CONTENT_TYPES = {
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".mjs": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class ArtifactStore:
    """Persists pipeline artifacts locally and optionally to S3."""

    def __init__(self, workdir: Path = None, s3_bucket: str = None):
        self.workdir = workdir or settings.WORKDIR
        self.s3_bucket = s3_bucket if s3_bucket is not None else settings.S3_BUCKET
        self.workdir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.workdir / name

    def write(self, name: str, content: str) -> Path:
        """Write content to an artifact file."""
        p = self.path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def read(self, name: str) -> str:
        p = self.path(name)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def exists(self, name: str) -> bool:
        return self.path(name).exists()

    def persist_all(self) -> List[str]:
        """Upload all artifacts in the working dir to S3 (if configured)."""
        if not self.s3_bucket:
            return []
        try:
            import boto3
            s3 = boto3.client("s3")
        except Exception as e:
            logger.warning("S3 upload disabled: %s", e)
            return []
        uploaded = []
        for name in os.listdir(self.workdir):
            p = self.path(name)
            if p.is_file():
                try:
                    s3.upload_file(
                        str(p), self.s3_bucket, f"sdd/{name}",
                        ExtraArgs={"ContentType": self._content_type(name)},
                    )
                    uploaded.append(name)
                except Exception as e:
                    logger.warning("Failed to upload %s: %s", name, e)
        return uploaded

    def _content_type(self, name: str) -> str:
        ext = os.path.splitext(name)[1].lower()
        return _CONTENT_TYPES.get(ext, "application/octet-stream")