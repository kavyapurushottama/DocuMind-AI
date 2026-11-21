"""
Local filesystem workspace and cache service for DocuMind AI.
Authoritative persistent document storage is maintained in PostgreSQL (`DocumentFile`).
This service provides local working cache for text extraction, chunking, and PDF viewing,
and is deterministically re-materialized from PostgreSQL if the container disk is wiped on restart.
"""
import os
import shutil
import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService(ABC):
    @abstractmethod
    def save(self, file_id: str, extension: str, content: bytes) -> str:
        """Save file content and return the persistent file path / URI."""
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        pass

    @abstractmethod
    def read(self, file_path: str) -> bytes:
        """Read and return file bytes."""
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Delete file from storage."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, file_id: str, extension: str, content: bytes) -> str:
        clean_ext = extension.lstrip(".")
        filename = f"{file_id}.{clean_ext}"
        destination = os.path.abspath(os.path.join(self.upload_dir, filename))
        with open(destination, "wb") as f:
            f.write(content)
        return destination

    def exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def read(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    def delete(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError as e:
                logger.warning("Failed to delete local file %s: %s", file_path, e)
                return False
        return False


# Singleton instance
_storage_instance: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorageService()
    return _storage_instance

