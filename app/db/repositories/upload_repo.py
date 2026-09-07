"""
SatQuery AI - Uploaded Image Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.db.models import UploadedImage, ImageMetadata


class UploadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, image_id: str) -> Optional[UploadedImage]:
        result = await self.db.execute(
            select(UploadedImage)
            .options(selectinload(UploadedImage.image_metadata))
            .where(UploadedImage.id == image_id)
        )
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, image_ids: List[str]) -> List[UploadedImage]:
        result = await self.db.execute(
            select(UploadedImage)
            .options(selectinload(UploadedImage.image_metadata))
            .where(UploadedImage.id.in_(image_ids))
        )
        return list(result.scalars().all())

    async def create(
        self,
        original_filename: str,
        storage_path: str,
        file_size_bytes: int,
        mime_type: str,
        file_format: str,
        modality: str = "optical",
        tag: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata_dict: Optional[Dict[str, Any]] = None
    ) -> UploadedImage:
        image = UploadedImage(
            original_filename=original_filename,
            storage_path=storage_path,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            file_format=file_format,
            modality=modality,
            tag=tag,
            user_id=user_id
        )
        self.db.add(image)
        await self.db.flush()

        if metadata_dict:
            img_meta = ImageMetadata(
                image_id=image.id,
                width=metadata_dict.get("width", 0),
                height=metadata_dict.get("height", 0),
                num_bands=metadata_dict.get("num_bands", 1),
                dtype=metadata_dict.get("dtype", "uint8"),
                crs=metadata_dict.get("crs"),
                transform=metadata_dict.get("transform"),
                bounds=metadata_dict.get("bounds"),
                resolution_x=metadata_dict.get("resolution_x"),
                resolution_y=metadata_dict.get("resolution_y"),
                acquisition_date=metadata_dict.get("acquisition_date"),
                sensor=metadata_dict.get("sensor"),
                is_georeferenced=metadata_dict.get("is_georeferenced", False),
                extra_metadata=metadata_dict.get("extra_metadata", {})
            )
            self.db.add(img_meta)

        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def delete(self, image_id: str) -> bool:
        image = await self.get_by_id(image_id)
        if not image:
            return False
        await self.db.delete(image)
        await self.db.commit()
        return True

    async def list_by_user(self, user_id: Optional[str] = None, limit: int = 50) -> List[UploadedImage]:
        query = select(UploadedImage).options(selectinload(UploadedImage.image_metadata))
        if user_id:
            query = query.where(UploadedImage.user_id == user_id)
        query = query.order_by(UploadedImage.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
