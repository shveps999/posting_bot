from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_post_notification_keyboard(
    post_id: int,
    is_liked: bool = False,
    url: str | None = None
) -> InlineKeyboardMarkup:
    """Клавиатура для уведомления о новом посте"""
    builder = InlineKeyboardBuilder()
    heart_text = "❤️ В избранном" if is_liked else "🤍 В избранное"
    builder.button(
        text=heart_text,
        callback_data=f"notify_heart_{post_id}"
    )
    if url:
        builder.button(text="🔗 Ссылка", url=url)
    builder.button(text="💌 Главное меню", callback_data="main_menu")

    if url:
        builder.adjust(2, 1)
    else:
        builder.adjust(1)

    return builder.as_markup()
