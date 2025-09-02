from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_post_notification_keyboard(
    post_id: int, url: str | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ В избранное", callback_data=f"notify_like_{post_id}")
    if url:
        builder.button(text="🔗 Открыть ссылку", url=url)
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()
