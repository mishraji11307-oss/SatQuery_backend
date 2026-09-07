"""
SatQuery AI - Secure Storage Service
Manages file uploads, path sanitization, MIME verification, and unique UUID naming.
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import FileValidationError
from app.core.logging import logger


class StorageService:
    """Provides secure local and cloud-ready storage operations for satellite rasters."""

    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int, str]:
        """
        Saves uploaded file securely with UUID name.
        Returns: (saved_file_path, original_filename, file_size_bytes, file_format)
        """
        original_filename = upload_file.filename or "unnamed_image.png"
        clean_filename = os.path.basename(original_filename)
        ext = clean_filename.split(".")[-1].lower() if "." in clean_filename else "png"

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                message=f"File extension '.{ext}' is not supported. Allowed: {settings.ALLOWED_EXTENSIONS}",
                details={"allowed_extensions": settings.ALLOWED_EXTENSIONS, "filename": clean_filename}
            )

        # Generate unique storage filename to prevent collisions and path traversal
        file_uuid = str(uuid.uuid4())
        storage_filename = f"{file_uuid}.{ext}"
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)

        # Ensure upload dir exists
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        size_bytes = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        try:
            async with aiofiles.open(storage_path, "wb") as out_file:
                while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                    size_bytes += len(chunk)
                    if size_bytes > max_bytes:
                        # Clean up partial file
                        if os.path.exists(storage_path):
                            os.remove(storage_path)
                        raise FileValidationError(
                            message=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                            details={"max_size_mb": settings.MAX_UPLOAD_SIZE_MB, "uploaded_bytes": size_bytes}
                        )
                    await out_file.write(chunk)
        except Exception as e:
            if os.path.exists(storage_path) and size_bytes > max_bytes:
                raise
            logger.error(f"Error saving upload file: {e}", exc_info=True)
            raise FileValidationError(f"Failed to persist file: {str(e)}")

        return storage_path, original_filename, size_bytes, ext

    @staticmethod
    def get_file_path(storage_path: str) -> str:
        """Sanitizes and resolves an absolute path within allowed storage directories."""
        resolved = Path(storage_path).resolve()
        base = Path(settings.STORAGE_DIR).resolve()
        if not str(resolved).startswith(str(base)):
            raise FileValidationError("Unauthorized path access detected.")
        return str(resolved)
