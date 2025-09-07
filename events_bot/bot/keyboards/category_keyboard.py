from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from events_bot.database.models import Category


def get_category_selection_keyboard(
    categories: List[Category], selected_ids: List[int] = None, for_post: bool = False
) -> InlineKeyboardMarkup:
    """Инлайн клавиатура для выбора категорий"""
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()

    # Используем разные префиксы для разных контекстов
    prefix = "post_category_" if for_post else "category_"

    for category in categories:
        is_selected = category.id in selected_ids
        checkbox = "⭐️" if is_selected else "▫️"
        display_name = getattr(category, "display_name", None) or category.name
        text = f"{display_name} {checkbox}"
        builder.button(text=text, callback_data=f"{prefix}{category.id}")

    # Располагаем по 2 в ряд
    builder.adjust(2)

    # Кнопки "Подтвердить" и "Отменить"
    if for_post:
        builder.row(
            InlineKeyboardButton(text="Подтвердить ✓", callback_data="confirm_post_categories")
        )
        builder.row(
            InlineKeyboardButton(text="Отменить ×", callback_data="cancel_post")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="Подтвердить ✓", callback_data="confirm_categories")
        )

    return builder.as_markup()
