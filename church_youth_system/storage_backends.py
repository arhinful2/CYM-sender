from urllib.parse import quote

import requests
from decouple import config
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

try:
    from vercel_blob import delete, head, put
except Exception:
    delete = None
    head = None
    put = None


@deconstructible
class VercelBlobStorage(Storage):
    """Django storage backend backed by Vercel Blob."""

    def __init__(self):
        self.token = config("BLOB_READ_WRITE_TOKEN", default="") or config(
            "VERCEL_BLOB_TOKEN", default="")
        self.base_url = config("VERCEL_BLOB_BASE_URL", default="").rstrip("/")

    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        return str(name).lstrip("/").replace("\\", "/")

    def _build_url(self, name: str) -> str:
        normalized = self._normalize_name(name)
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized

        # If only a pathname is stored and a token is available, try resolving public URL.
        if self.token and head:
            try:
                metadata = head(normalized, {"token": self.token})
                resolved_url = metadata.get("url", "")
                if resolved_url:
                    return resolved_url
            except Exception:
                pass

        if not self.base_url:
            # Fallback to MEDIA-style URL when explicit blob base URL is not configured.
            return f"/media/{normalized}"
        return f"{self.base_url}/{quote(normalized)}"

    def _save(self, name, content):
        if not self.token or not put:
            raise ValueError(
                "BLOB_READ_WRITE_TOKEN or VERCEL_BLOB_TOKEN is required for Vercel Blob storage.")

        normalized_name = self._normalize_name(name)
        blob = put(
            normalized_name,
            content.read(),
            {
                "token": self.token,
                "allowOverwrite": True,
                "addRandomSuffix": False,
            },
        )
        # Persist full public URL when available so rendering does not depend on extra env configuration.
        return blob.get("url") or blob.get("pathname", normalized_name)

    def delete(self, name):
        if not name or not self.token or not delete:
            return
        delete(self._build_url(name), {"token": self.token})

    def exists(self, name):
        if not name or not self.token or not head:
            return False
        try:
            head(self._build_url(name), {"token": self.token})
            return True
        except Exception:
            return False

    def size(self, name):
        if not name or not self.token or not head:
            return 0
        try:
            metadata = head(self._build_url(name), {"token": self.token})
            return int(metadata.get("size", 0))
        except Exception:
            return 0

    def url(self, name):
        return self._build_url(name)

    def open(self, name, mode="rb"):
        response = requests.get(self._build_url(name), timeout=20)
        response.raise_for_status()
        return ContentFile(response.content, name=name)

    def path(self, name):
        raise NotImplementedError(
            "Vercel Blob storage does not support local file paths.")
