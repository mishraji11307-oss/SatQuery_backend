"""
SatQuery AI - Imagery Upload & Metadata Management APIs
"""
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.upload_repo import UploadRepository
from app.db.models import User
from app.services.storage_service import StorageService
from app.services.metadata_service import MetadataService
from app.schemas.response import APIResponse
from app.schemas.upload import UploadResponse, ImageMetadataSchema, UploadListResponse
from app.api.dependencies import get_optional_user
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/uploads", tags=["Imagery Uploads"])


@router.post("", response_model=APIResponse[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_satellite_image(
    request: Request,
    file: UploadFile = File(...),
    modality: Optional[str] = Form(None),
    tag: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads remote sensing imagery (GeoTIFF, TIFF, PNG, JPEG), inspects raster properties,
    and returns rich geospatial metadata.
    """
    # 1. Save file securely with UUID name
    saved_path, original_filename, size_bytes, ext = await StorageService.save_upload_file(file)

    # 2. Extract geospatial metadata
    meta = MetadataService.extract_image_metadata(saved_path, original_filename=original_filename)
    final_modality = modality if modality else meta.get("modality", "optical")
    meta["modality"] = final_modality

    # 3. Store in DB
    upload_repo = UploadRepository(db)
    user_id = current_user.id if current_user else None
    
    img_record = await upload_repo.create(
        original_filename=original_filename,
        storage_path=saved_path,
        file_size_bytes=size_bytes,
        mime_type=file.content_type or f"image/{ext}",
        file_format=ext,
        modality=final_modality,
        tag=tag,
        user_id=user_id,
        metadata_dict=meta
    )

    # Convert to response schema
    meta_schema = ImageMetadataSchema(
        width=meta.get("width", 0),
        height=meta.get("height", 0),
        num_bands=meta.get("num_bands", 1),
        dtype=meta.get("dtype", "uint8"),
        crs=meta.get("crs"),
        transform=meta.get("transform"),
        bounds=meta.get("bounds"),
        resolution_x=meta.get("resolution_x"),
        resolution_y=meta.get("resolution_y"),
        acquisition_date=meta.get("acquisition_date"),
        sensor=meta.get("sensor"),
        is_georeferenced=meta.get("is_georeferenced", False),
        extra_metadata=meta.get("extra_metadata")
    )

    rel_filename = os.path.basename(saved_path)
    preview_url = f"/storage/uploads/{rel_filename}"

    res = UploadResponse(
        id=img_record.id,
        original_filename=img_record.original_filename,
        file_size_bytes=img_record.file_size_bytes,
        mime_type=img_record.mime_type,
        file_format=img_record.file_format,
        modality=img_record.modality,
        tag=img_record.tag,
        created_at=img_record.created_at,
        metadata=meta_schema,
        preview_url=preview_url
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=res, request_id=request_id)


@router.get("", response_model=APIResponse[UploadListResponse])
async def list_uploaded_images(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists recent uploaded imagery."""
    upload_repo = UploadRepository(db)
    user_id = current_user.id if current_user else None
    images = await upload_repo.list_by_user(user_id=user_id, limit=50)

    items = []
    for img in images:
        meta_schema = None
        if img.image_metadata:
            meta_schema = ImageMetadataSchema.model_validate(img.image_metadata)
        
        rel_filename = os.path.basename(img.storage_path)
        items.append(
            UploadResponse(
                id=img.id,
                original_filename=img.original_filename,
                file_size_bytes=img.file_size_bytes,
                mime_type=img.mime_type,
                file_format=img.file_format,
                modality=img.modality,
                tag=img.tag,
                created_at=img.created_at,
                metadata=meta_schema,
                preview_url=f"/storage/uploads/{rel_filename}"
            )
        )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=UploadListResponse(total=len(items), images=items),
        request_id=request_id
    )


@router.get("/{image_id}", response_model=APIResponse[UploadResponse])
async def get_uploaded_image(
    image_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves an image's upload details and metadata."""
    upload_repo = UploadRepository(db)
    img = await upload_repo.get_by_id(image_id)
    if not img:
        raise EntityNotFoundError("UploadedImage", image_id)

    meta_schema = None
    if img.image_metadata:
        meta_schema = ImageMetadataSchema.model_validate(img.image_metadata)

    rel_filename = os.path.basename(img.storage_path)
    res = UploadResponse(
        id=img.id,
        original_filename=img.original_filename,
        file_size_bytes=img.file_size_bytes,
        mime_type=img.mime_type,
        file_format=img.file_format,
        modality=img.modality,
        tag=img.tag,
        created_at=img.created_at,
        metadata=meta_schema,
        preview_url=f"/storage/uploads/{rel_filename}"
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data=res, request_id=request_id)


@router.get("/{image_id}/metadata", response_model=APIResponse[ImageMetadataSchema])
async def get_image_metadata(
    image_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves detailed raster and geospatial attributes."""
    upload_repo = UploadRepository(db)
    img = await upload_repo.get_by_id(image_id)
    if not img or not img.image_metadata:
        raise EntityNotFoundError("ImageMetadata", image_id)

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=ImageMetadataSchema.model_validate(img.image_metadata),
        request_id=request_id
    )


@router.delete("/{image_id}", response_model=APIResponse[dict])
async def delete_image(
    image_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deletes an uploaded image record and its associated raster file."""
    upload_repo = UploadRepository(db)
    img = await upload_repo.get_by_id(image_id)
    if not img:
        raise EntityNotFoundError("UploadedImage", image_id)

    # Remove file from disk
    if os.path.exists(img.storage_path):
        try:
            os.remove(img.storage_path)
        except Exception:
            pass

    await upload_repo.delete(image_id)
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(success=True, data={"deleted": True, "id": image_id}, request_id=request_id)
