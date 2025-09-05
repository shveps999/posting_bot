from typing import List
import logfire
from ..repositories import UserRepository
from ..models import User, Post
from ...utils import get_clean_category_string


class NotificationService:
    """Асинхронный сервис для работы с уведомлениями"""

    @staticmethod
    async def get_users_to_notify(db, post: Post) -> List[User]:
        """Получить пользователей для уведомления о новом посте"""
        # Загружаем связанные объекты
        await db.refresh(post, attribute_names=["author", "categories"])

        # Получаем пользователей по городу поста и категориям поста
        post_city = getattr(post, "city", None)
        category_ids = [cat.id for cat in post.categories]
        logfire.info(
            f"Ищем пользователей для уведомления: город={post_city}, категории={category_ids}"
        )

        users = await UserRepository.get_users_by_city_and_categories(
            db, post_city, category_ids
        )
        # Включаем автора поста в список уведомляемых
        logfire.info(
            f"Найдено {len(users)} пользователей для уведомления (включая автора)"
        )
        return users

    @staticmethod
    def format_post_notification(post: Post) -> str:
        """Форматировать уведомление о посте"""
        # Безопасно получаем данные, избегая ленивой загрузки
        # Получаем названия категорий без эмодзи для чистого текста
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

        event_at = getattr(post, "event_at", None)
        if event_at:
            # event_at теперь хранится в МСК, показываем как есть
            event_str = event_at.strftime("%d.%m.%Y %H:%M")
        else:
            event_str = ""

        event_line = f"Событие: {event_str} (МСК)" if event_str else ""

        return (
            f"⭐️ <i>{category_str}</i>\n"
            f"<b>{post.title}</b>\n\n"
            f"<i> 🗓 {event_str}</i>\n"
            f"<i>📍 {getattr(post, 'address', 'Не указан')}</i>\n\n"
            f"{post.content}\n\n"
        )
