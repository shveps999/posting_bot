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
        [KeyboardButton(text="✅ Подтвердить выбор")],
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

    # Создаем кнопки с правильным выравниванием
    from events_bot.utils import visual_len

    MAX_NAME_LENGTH = 18  # Максимальная длина названия

    for category in categories:
        is_selected = category.id in selected_ids
        checkbox = "⭐" if is_selected else "⬜"

        # Используем display_name для UI (с эмодзи), fallback на name
        display_name = getattr(category, "display_name", None) or category.name
        
        # Обрезаем название если слишком длинное
        if visual_len(display_name) > MAX_NAME_LENGTH:
            # Обрезаем с учетом эмодзи
            import re
            
            clean_length = 0
            result = ""
            for char in display_name:
                if re.match(r'[\U0001F000-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', char):
                    # Эмодзи не считаем в длину
                    result += char
                else:
                    if clean_length < MAX_NAME_LENGTH - 1:
                        result += char
                        clean_length += 1
                    else:
                        result += "…"
                        break
            display_name = result

        # Фиксированная ширина - используем пробелы для выравнивания
        name_visual_len = visual_len(display_name)
        # Добавляем пробелы для выравнивания (18 символов для названия + 2 для чекбокса)
        spaces_needed = max(1, 20 - name_visual_len)
        padding = " " * spaces_needed
        
        text = f"{display_name}{padding}{checkbox}"
        builder.button(text=text, callback_data=f"{prefix}{category.id}")
    builder.adjust(2)

    confirm_callback = "confirm_post_categories" if for_post else "confirm_categories"

    buttons = [InlineKeyboardButton(text="Подтвердить", callback_data=confirm_callback)]

    if for_post:
        buttons.append(
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post")
        )

    builder.row(*buttons)
    return builder.as_markup()
