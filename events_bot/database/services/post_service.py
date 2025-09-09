from typing import List, Optional
import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from ..repositories import PostRepository
from ..models import Post

class PostService:
    """Асинхронный сервис для работы с постами"""
    
    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        cities: List[str],
        image_id: Optional[str] = None,
        event_at: Optional[datetime] = None,
        url: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Post:
        """Создать новый пост"""
        logfire.info(
            f"Создание поста пользователем {author_id}: {title}"
        )
        return await PostRepository.create_post(
            db=db,
            title=title,
            content=content,
            author_id=author_id,
            category_ids=category_ids,
            cities=cities,
            image_id=image_id,
            event_at=event_at,
            url=url,
            address=address,
        )
    
    @staticmethod
    async def get_post_cities(db: AsyncSession, post_id: int) -> List[str]:
        """Получить список городов поста"""
        return await PostRepository.get_post_cities(db, post_id)
    
    @staticmethod
    async def get_pending_moderation(db: AsyncSession) -> List[Post]:
        """Получить посты, ожидающие модерации"""
        return await PostRepository.get_pending_moderation(db)
    
    @staticmethod
    async def get_approved_posts(db: AsyncSession) -> List[Post]:
        """Получить одобренные посты"""
        return await PostRepository.get_approved_posts(db)
    
    @staticmethod
    async def get_posts_by_categories(db: AsyncSession, category_ids: List[int]) -> List[Post]:
        """Получить посты по категориям"""
        return await PostRepository.get_posts_by_categories(db, category_ids)
    
    @staticmethod
    async def approve_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Одобрить пост"""
        logfire.info(f"Пост {post_id} одобрен модератором {moderator_id}")
        return await PostRepository.approve_post(db, post_id, moderator_id, comment)
    
    @staticmethod
    async def reject_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Отклонить пост"""
        logfire.info(f"Пост {post_id} отклонен модератором {moderator_id}")
        return await PostRepository.reject_post(db, post_id, moderator_id, comment)
    
    @staticmethod
    async def request_changes(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        """Запросить изменения в посте"""
        logfire.info(f"Запрошены изменения в посте {post_id} модератором {moderator_id}")
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
    async def publish_post(db: AsyncSession, post_id: int) -> Post:
        """Опубликовать пост"""
        return await PostRepository.publish_post(db, post_id)
    
    @staticmethod
    async def get_feed_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        """Получить посты для ленты пользователя"""
        return await PostRepository.get_feed_posts(db, user_id, limit, offset)
    
    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество постов для ленты пользователя"""
        return await PostRepository.get_feed_posts_count(db, user_id)
    
    @staticmethod
    async def get_liked_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        """Получить избранные посты пользователя"""
        return await PostRepository.get_liked_posts(db, user_id, limit, offset)
    
    @staticmethod
    async def get_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество избранных постов пользователя"""
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
        """Удалить пост"""
        return await PostRepository.delete_post(db, post_id)
