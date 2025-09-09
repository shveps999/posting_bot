from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_moderation_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для модерации поста"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"moderate_approve_{post_id}")
    builder.button(text="❌ Отклонить", callback_data=f"moderate_reject_{post_id}")
    builder.button(text="✏️ Запросить изменения", callback_data=f"moderate_request_changes_{post_id}")
    builder.adjust(1)
    return builder.as_markup()
