"""Local file system based object storage adapter.

Object key convention (agreed in Step 0):
    offering/{offering_id}/assignment/{assignment_id}/student/{student_id}/attempt/{no}/{filename}

Replacing with MinIO or other external storage later only requires
swapping this adapter while keeping the same interface.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Union


class LocalStorageAdapter:
    """Adapter that treats a local directory as an object storage.

    Args:
        storage_root: Root directory where files will be stored.
                      Pass the value of the LOCAL_STORAGE_ROOT env var.
    """

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.root = Path(storage_root).resolve()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_file(self, local_path: Union[str, Path], object_key: str) -> str:
        """Copy an existing file to the object_key path inside storage_root.

        Args:
            local_path: Absolute or relative path to the source file.
            object_key: Relative key representing the destination.
                        e.g. "offering/abc/assignment/hw1/student/S001/attempt/1/hw1.py"

        Returns:
            Absolute path string of the stored file.

        Raises:
            FileNotFoundError: If the source file does not exist.
        """
        src = Path(local_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        dest = self._resolve_dest(object_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return str(dest)

    def save_json(self, data: dict, object_key: str) -> str:
        """Serialize a dict to JSON and write it to the object_key path.

        Args:
            data: Dictionary to serialize.
            object_key: Relative key representing the destination.

        Returns:
            Absolute path string of the stored file.
        """
        dest = self._resolve_dest(object_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(dest)

    def load_text(self, object_key: str) -> str:
        """Return the text content of the file at object_key.

        Args:
            object_key: Relative key of the file to read.

        Returns:
            Text content of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        dest = self._resolve_dest(object_key)
        if not dest.exists():
            raise FileNotFoundError(f"Stored file not found: {dest}")
        return dest.read_text(encoding="utf-8")

    def exists(self, object_key: str) -> bool:
        """Check whether a file exists at the given object_key.

        Args:
            object_key: Relative key to check.

        Returns:
            True if the file exists, False otherwise.
        """
        return self._resolve_dest(object_key).exists()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_dest(self, object_key: str) -> Path:
        """Resolve object_key to an absolute path under storage_root."""
        # Strip leading slash to ensure path stays under root
        return self.root / object_key.lstrip("/")
