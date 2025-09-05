from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..repositories import PostRepository, ModerationRepository
from ..models import Post, ModerationAction
from ...utils import get_clean_category_string


class ModerationService:
    """Асинхронный сервис для работы с модерацией"""

    @staticmethod
    async def get_moderation_queue(db: AsyncSession) -> List[Post]:
        """Получить очередь модерации"""
        return await PostRepository.get_pending_moderation(db)

    @staticmethod
    async def get_moderation_history(db: AsyncSession, post_id: int) -> List:
        """Получить историю модерации поста"""
        return await ModerationRepository.get_moderation_history(db, post_id)

    @staticmethod
    async def get_actions_by_type(db: AsyncSession, action: ModerationAction) -> List:
        """Получить записи модерации по типу действия"""
        return await ModerationRepository.get_actions_by_type(db, action)

    @staticmethod
    def format_post_for_moderation(post: Post) -> str:
        """Форматировать пост для модерации"""
        # Безопасно получаем данные
        category_str = get_clean_category_string(
            post.categories if hasattr(post, "categories") else None
        )

        author_name = "Аноним"
        if hasattr(post, "author") and post.author is not None:
            author = post.author
            author_name = (
                getattr(author, "first_name", None)
                or getattr(author, "username", None)
                or "Аноним"
            )

        post_city = getattr(post, "city", "Не указан")
        address = getattr(post, "address", "Не указан")
        url = getattr(post, "url", None)

        event_at = getattr(post, "event_at", None)
        event_str = event_at.strftime("%d.%m.%Y %H:%M") if event_at else "Не указано"

        created_at = getattr(post, "created_at", None)
        created_str = created_at.strftime("%d.%m.%Y %H:%M") if created_at else "Не указано"

        # Формируем текст с HTML-разметкой
        lines = [
            f"<b>Пост на модерацию</b>",
            "",
            f"<b>{post.title}</b>",
            f"<i>⭐️ {category_str}</i>",
            f"<i>🗓 {event_str}</i>",
            "",
            f"📍 <b>Город:</b> {post_city}",
            f"📌 <b>Адрес:</b> {address}",
        ]

        # Добавляем ссылку, если есть
        if url:
            lines.append(f"🔗 {url}")

        lines.extend([
            "",
            f"<i>{post.content}</i>",
        ])

        return "\n".join(lines)

    @staticmethod
    def get_action_display_name(action: ModerationAction) -> str:
        """Получить отображаемое имя действия"""
        action_names = {
            ModerationAction.APPROVE: "Одобрено",
            ModerationAction.REJECT: "Отклонено",
            ModerationAction.REQUEST_CHANGES: "Требуются изменения",
        }
        return action_names.get(action, "Неизвестно")
