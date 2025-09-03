from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List
from events_bot.database.models import Category
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_category_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора категорий"""
    keyboard = [
        [KeyboardButton(text="☑️ Подтвердить выбор")],
        [KeyboardButton(text="🔙 Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


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

        # Используем display_name для UI (с эмодзи), fallback на name
        display_name = getattr(category, "display_name", None) or category.name

        text = f"{display_name} {checkbox}"
        builder.button(text=text, callback_data=f"{prefix}{category.id}")
    builder.adjust(2)

    confirm_callback = "confirm_post_categories" if for_post else "confirm_categories"

    # Создаём список кнопок: сначала "Отмена", потом "Подтвердить"
    buttons = []

    if for_post:
        buttons.append(
            InlineKeyboardButton(text="Отменить", callback_data="cancel_post")
        )

    buttons.append(
        InlineKeyboardButton(text="Подтвердить", callback_data=confirm_callback)
    )

    # Добавляем обе кнопки в одну строку
    builder.row(*buttons)
    return builder.as_markup()
