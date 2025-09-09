from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from events_bot.database.models import Post, ModerationRecord, Like
from events_bot.database.repositories import PostRepository
from typing import List, Optional
from datetime import datetime


class PostService:
    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        city: str | None = None,
        image_id: str | None = None,
        event_at: datetime | None = None,
        url: str | None = None,
        address: str | None = None,
    ) -> Post:
        """Создать новый пост"""
        return await PostRepository.create_post(
            db, title, content, author_id, category_ids,
            city, image_id, event_at, url, address
        )

    @staticmethod
    async def get_pending_moderation(db: AsyncSession) -> List[Post]:
        """Получить посты на модерации"""
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def approve_post(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        """Одобрить пост"""
        return await PostRepository.approve_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def reject_post(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        """Отклонить пост"""
        return await PostRepository.reject_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def request_changes(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        """Запросить изменения"""
        return await PostRepository.request_changes(db, post_id, moderator_id, comment)

    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        """Получить посты пользователя"""
        return await PostRepository.get_user_posts(db, user_id)

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        """Получить пост по ID"""
        return await PostRepository.get_post_by_id(db, post_id)

    @staticmethod
    async def get_approved_posts(db: AsyncSession) -> List[Post]:
        """Получить одобренные посты"""
        return await PostRepository.get_approved_posts(db)

    @staticmethod
    async def get_posts_by_categories(db: AsyncSession, category_ids: List[int]) -> List[Post]:
        """Получить посты по категориям"""
        return await PostRepository.get_posts_by_categories(db, category_ids)

    @staticmethod
    async def get_feed_posts(db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0) -> List[Post]:
        """Получить посты для ленты"""
        return await PostRepository.get_feed_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество постов для ленты"""
        return await PostRepository.get_feed_posts_count(db, user_id)

    @staticmethod
    async def get_liked_posts(db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0) -> List[Post]:
        """Получить понравившиеся посты"""
        return await PostRepository.get_liked_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество понравившихся постов"""
        return await PostRepository.get_liked_posts_count(db, user_id)

    @staticmethod
    async def delete_expired_posts(db: AsyncSession) -> int:
        """Удалить просроченные посты"""
        return await PostRepository.delete_expired_posts(db)

    @staticmethod
    async def get_expired_posts_info(db: AsyncSession) -> list[dict]:
        """Получить информацию о просроченных постах"""
        return await PostRepository.get_expired_posts_info(db)

    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int) -> bool:
        """Удалить пост по ID"""
        return await PostRepository.delete_post(db, post_id)
