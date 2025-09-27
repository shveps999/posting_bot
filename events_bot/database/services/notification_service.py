from typing import List
import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..repositories import UserRepository
from ..models import User, Post, Like
from ...utils import get_clean_category_string
from ...bot.keyboards.notification_keyboard import get_post_notification_keyboard
from ...storage import file_storage
from aiogram import Bot


class NotificationService:
    """Асинхронный сервис для работы с уведомлениями"""

    @staticmethod
    async def get_users_to_notify(db: AsyncSession, post: Post) -> List[User]:
        """Получить пользователей для уведомления о новом посте"""
        await db.refresh(post, attribute_names=["author", "categories", "cities"])

        city_ids = [c.id for c in post.cities]
        category_ids = [cat.id for cat in post.categories]
        logfire.info(
            f"Ищем пользователей для уведомления: города={city_ids}, категории={category_ids}"
        )

        users = await UserRepository.get_users_by_cities_and_categories(
            db, city_ids, category_ids
        )
        logfire.info(
            f"Найдено {len(users)} пользователей для уведомления"
        )
        return users

    @staticmethod
    def format_post_notification(post: Post) -> str:
        """Форматировать уведомление о посте"""
        category_str = get_clean_category_string(
            post.categories if hasattr(post, "categories") else None
        )
        event_at = getattr(post, "event_at", None)
        event_str = event_at.strftime("%d.%m.%Y %H:%M") if event_at else ""
        
        city_names = [c.name for c in post.cities] if hasattr(post, "cities") else []
        post_city = ", ".join(city_names) or "Не указан"
        address = getattr(post, "address", "Не указан")

        lines = [
            f"⭐️ <i>{category_str}</i>",
            "",
            f"<b>{post.title}</b>",
            "",
        ]
        if event_str:
            lines.append(f"<i> 🗓 {event_str}</i>")
        lines.append(f"<i>📍 {address}</i>")
        lines.append(f"<i>🎓 {post_city}</i>")
        lines.append("")
        lines.append(f"{post.content}")

        return "\n".join(lines)

    @staticmethod
    async def send_post_notification(bot: Bot, post: Post, users: List[User], db: AsyncSession) -> None:
        """Отправить уведомления о новом посте"""
        logfire.info(f"Отправляем уведомления о посте {post.id} {len(users)} пользователям")
        
        await db.refresh(post, attribute_names=["author", "categories", "cities"])
        
        notification_text = NotificationService.format_post_notification(post)
        post_url = getattr(post, "url", None)

        success_count = 0
        error_count = 0

        for user in users:
            try:
                logfire.debug(f"Отправляем уведомление пользователю {user.id}")

                is_liked = await db.scalar(
                    select(Like.id).where(Like.user_id == user.id, Like.post_id == post.id)
                ) is not None

                keyboard = get_post_notification_keyboard(
                    post_id=post.id,
                    is_liked=is_liked,
                    url=post_url,
                )

                if post.image_id:
                    media_photo = await file_storage.get_media_photo(post.image_id)
                    if media_photo:
                        await bot.send_photo(
                            chat_id=user.id,
                            photo=media_photo.media,
                            caption=notification_text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    else:
                        await bot.send_message(
                            chat_id=user.id,
                            text=notification_text,
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                else:
                    await bot.send_message(
                        chat_id=user.id,
                        text=notification_text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )

                success_count += 1
            except Exception as e:
                logfire.warning(f"Ошибка отправки уведомления пользователю {user.id}: {e}")
                error_count += 1

        logfire.info(f"Уведомления отправлены: успех={success_count}, ошибок={error_count}")
