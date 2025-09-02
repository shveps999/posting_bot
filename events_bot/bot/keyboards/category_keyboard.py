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

    # Создаем кнопки с правильным выравниванием эмодзи
    from events_bot.utils import visual_len

    BUTTON_WIDTH = 18  # Фиксированная визуальная ширина кнопки

    for category in categories:
        is_selected = category.id in selected_ids
        checkbox = "⭐️" if is_selected else "⬜"

        name = category.name
        name_len = visual_len(name)  # Визуальная длина без учета эмодзи

        # Если название слишком длинное, обрезаем
        if name_len > BUTTON_WIDTH - 3:
            # Нужно аккуратно обрезать с учетом эмодзи
            import re

            # Разделяем эмодзи и текст
            parts = re.split(
                r"([\U0001F000-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+)",
                name,
            )

            new_name = ""
            current_len = 0
            for part in parts:
                part_len = (
                    len(part)
                    if re.match(
                        r"[\U0001F000-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+",
                        part,
                    )
                    else len(part)
                )
                if current_len + part_len <= BUTTON_WIDTH - 4:  # -4 для "…" и чекбокса
                    new_name += part
                    current_len += part_len
                else:
                    if current_len < BUTTON_WIDTH - 4:
                        remaining = BUTTON_WIDTH - 4 - current_len
                        new_name += part[:remaining] + "…"
                    break
            name = new_name
            name_len = visual_len(name)

        # Добавляем точки для выравнивания чекбокса справа
        dots_count = BUTTON_WIDTH - name_len - 2  # -2 для пробела и чекбокса
        dots = "·" * max(0, dots_count)

        text = f"{name} {dots}{checkbox}"
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
