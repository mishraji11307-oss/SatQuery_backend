"""
SatQuery AI - Query Record Repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import QueryRecord


class QueryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, query_id: str) -> Optional[QueryRecord]:
        result = await self.db.execute(select(QueryRecord).where(QueryRecord.id == query_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        query_text: str,
        detected_intent: str,
        task_type: str,
        intent_confidence: float = 1.0,
        user_id: Optional[str] = None,
        planner_output: Optional[Dict[str, Any]] = None
    ) -> QueryRecord:
        record = QueryRecord(
            query_text=query_text,
            detected_intent=detected_intent,
            task_type=task_type,
            intent_confidence=intent_confidence,
            user_id=user_id,
            planner_output=planner_output
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_recent(self, user_id: Optional[str] = None, limit: int = 50) -> List[QueryRecord]:
        query = select(QueryRecord)
        if user_id:
            query = query.where(QueryRecord.user_id == user_id)
        query = query.order_by(QueryRecord.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
