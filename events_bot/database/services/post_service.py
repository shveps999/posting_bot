from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from ..repositories import PostRepository
from ..models import Post
import os
import logfire
from events_bot.bot.keyboards.moderation_keyboard import get_moderation_keyboard
from events_bot.storage import file_storage
from aiogram.types import InputMediaPhoto
from .moderation_service import ModerationService

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


class PostService:
    """Асинхронный сервис для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        city: str | None = None,
        image_id: str | None = None,
        event_at: str | None = None,
        url: str | None = None,
        address: str | None = None,
    ) -> Post:
        """Создать новый пост"""
        parsed_event_at = None
        if event_at is not None:
            try:
                parsed_event_at = datetime.fromisoformat(event_at)
                if parsed_event_at.tzinfo is not None:
                    parsed_event_at = parsed_event_at.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                parsed_event_at = None

        return await PostRepository.create_post(
            db, title, content, author_id, category_ids, city, image_id, parsed_event_at, url, address
        )

    @staticmethod
    async def create_post_and_send_to_moderation(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        city: str | None = None,
        image_id: str | None = None,
        event_at: str | None = None,
        url: str | None = None,
        address: str | None = None,
        bot=None,
    ) -> Post:
        """Создать пост и отправить на модерацию"""
        post = await PostService.create_post(
            db, title, content, author_id, category_ids, city, image_id, event_at, url, address
        )
        if post and bot:
            await PostService.send_post_to_moderation(bot, post, db)
        return post

    @staticmethod
    async def send_post_to_moderation(bot, post: Post, db=None):
        """Отправить пост на модерацию"""
        moderation_group_id = os.getenv("MODERATION_GROUP_ID")
        logfire.info(f"MODERATION_GROUP_ID: {moderation_group_id}")

        if not moderation_group_id:
            logfire.error("MODERATION_GROUP_ID не установлен")
            return

        if db:
            await db.refresh(post, attribute_names=["author", "categories"])

        moderation_text = ModerationService.format_post_for_moderation(post)
        moderation_keyboard = get_moderation_keyboard(post.id)

        logfire.info(f"Отправляем пост {post.id} на модерацию в группу {moderation_group_id}")

        try:
            if post.image_id:
                media_photo = await file_storage.get_media_photo(post.image_id)
                if media_photo:
                    await bot.send_photo(
                        chat_id=moderation_group_id,
                        photo=media_photo.media,
                        caption=moderation_text,
                        reply_markup=moderation_keyboard,
                        parse_mode="HTML",
                    )
                    logfire.info("Пост с изображением отправлен на модерацию")
                    return

            await bot.send_message(
                chat_id=moderation_group_id,
                text=moderation_text,
                reply_markup=moderation_keyboard,
                parse_mode="HTML",
            )
            logfire.info("Пост без изображения отправлен на модерацию")
        except Exception as e:
            logfire.error(f"Ошибка отправки поста на модерацию: {e}")
            import traceback
            logfire.error(f"Стек ошибки: {traceback.format_exc()}")

    # Остальные методы без изменений
    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        return await PostRepository.get_user_posts(db, user_id)

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        return await PostRepository.get_post_by_id(db, post_id)

    @staticmethod
    async def get_posts_by_categories(db: AsyncSession, category_ids: list[int]) -> list[Post]:
        return await PostRepository.get_posts_by_categories(db, category_ids)

    @staticmethod
    async def get_pending_moderation_posts(db: AsyncSession) -> List[Post]:
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def approve_post(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        return await PostRepository.approve_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def publish_post(db: AsyncSession, post_id: int) -> Post:
        return await PostRepository.publish_post(db, post_id)

    @staticmethod
    async def reject_post(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        return await PostRepository.reject_post(db, post_id, moderator_id, comment)

    @staticmethod
    async def request_changes(db: AsyncSession, post_id: int, moderator_id: int, comment: str = None) -> Post:
        return await PostRepository.request_changes(db, post_id, moderator_id, comment)

    @staticmethod
    async def get_feed_posts(db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0) -> List[Post]:
        return await PostRepository.get_feed_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        return await PostRepository.get_feed_posts_count(db, user_id)

    @staticmethod
    async def get_liked_posts(db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0) -> List[Post]:
        return await PostRepository.get_liked_posts(db, user_id, limit, offset)

    @staticmethod
    async def get_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        return await PostRepository.get_liked_posts_count(db, user_id)

    @staticmethod
    async def delete_expired_posts(db: AsyncSession) -> int:
        return await PostRepository.delete_expired_posts(db)

    @staticmethod
    async def get_expired_posts_info(db: AsyncSession) -> list[dict]:
        return await PostRepository.get_expired_posts_info(db)
