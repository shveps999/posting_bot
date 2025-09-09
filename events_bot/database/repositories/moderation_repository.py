from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..models import ModerationRecord


class ModerationRepository:
    """Асинхронный репозиторий для работы с модерацией"""

    @staticmethod
    async def get_moderation_history(
        db: AsyncSession, post_id: int
    ) -> List[ModerationRecord]:
        """Получить историю модерации поста"""
        result = await db.execute(
            select(ModerationRecord)
            .where(ModerationRecord.post_id == post_id)
            .order_by(ModerationRecord.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_moderator_actions(
        db: AsyncSession, moderator_id: int
    ) -> List[ModerationRecord]:
        """Получить действия модератора"""
        result = await db.execute(
            select(ModerationRecord)
            .where(ModerationRecord.moderator_id == moderator_id)
            .order_by(ModerationRecord.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_actions_by_type(
        db: AsyncSession, action: int
    ) -> List[ModerationRecord]:
        """Получить действия по типу (1=APPROVE, 2=REJECT, 3=REQUEST_CHANGES)"""
        result = await db.execute(
            select(ModerationRecord)
            .where(ModerationRecord.action == action)
            .order_by(ModerationRecord.created_at.desc())
        )
        return result.scalars().all()
