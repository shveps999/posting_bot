from typing import List
import logfire
from ..repositories import UserRepository
from ..models import User, Post


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
        category_names = []
        if hasattr(post, "categories") and post.categories is not None:
            category_names = [
                getattr(cat, "name", "Неизвестно") for cat in post.categories
            ]

        category_str = ", ".join(category_names) if category_names else "Неизвестно"

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
            # Переводим время из UTC в МСК для отображения
            try:
                from zoneinfo import ZoneInfo
                from datetime import timezone, timedelta

                if ZoneInfo:
                    msk = ZoneInfo("Europe/Moscow")
                    event_at_msk = event_at.replace(tzinfo=timezone.utc).astimezone(msk)
                    event_str = event_at_msk.strftime("%d.%m.%Y %H:%M")
                else:
                    # Fallback: добавляем 3 часа к UTC времени
                    event_at_msk = event_at + timedelta(hours=3)
                    event_str = event_at_msk.strftime("%d.%m.%Y %H:%M")
            except Exception:
                # Fallback при ошибке
                from datetime import timedelta

                event_at_msk = event_at + timedelta(hours=3)
                event_str = event_at_msk.strftime("%d.%m.%Y %H:%M")
        else:
            event_str = ""

        event_line = f"Событие: {event_str} (МСК)" if event_str else ""

        return (
            f"Новый пост в категориях '{category_str}'\n\n"
            f"{post.title}\n\n"
            f"{post.content}\n\n"
            f"Автор: {author_name}\n"
            f"{event_line}"
        )
