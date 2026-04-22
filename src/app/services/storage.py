"""Local file storage abstraction for material files."""

import os
from pathlib import Path

# Default storage directory - can be overridden via environment variable
STORAGE_BASE_DIR = os.environ.get("MATERIAL_STORAGE_DIR", "/tmp/koiboi_materials")


class StorageService:
    """Simple local filesystem storage for material PDF files."""

    @staticmethod
    def _full_path(storage_key: str) -> Path:
        """Resolve the full filesystem path for a given storage_key."""
        return Path(STORAGE_BASE_DIR) / storage_key

    @staticmethod
    def save_file(content: bytes, storage_key: str) -> None:
        """
        Save file content to local storage.

        Args:
            content: Raw file bytes
            storage_key: Relative path used as the storage key
                         (e.g. materials/{user_id}/{material_id}/{filename})
        """
        full_path = StorageService._full_path(storage_key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)

    @staticmethod
    def get_file(storage_key: str) -> bytes:
        """
        Retrieve file content from local storage.

        Args:
            storage_key: Relative path used as the storage key

        Returns:
            Raw file bytes

        Raises:
            FileNotFoundError: If the file does not exist in storage
        """
        full_path = StorageService._full_path(storage_key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found in storage: {storage_key}")
        return full_path.read_bytes()

    @staticmethod
    def delete_file(storage_key: str) -> None:
        """
        Delete a file from local storage. Silently ignores missing files.

        Args:
            storage_key: Relative path used as the storage key
        """
        full_path = StorageService._full_path(storage_key)
        try:
            full_path.unlink()
        except FileNotFoundError:
            pass
