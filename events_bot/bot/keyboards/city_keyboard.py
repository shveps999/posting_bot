from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from events_bot.database.models import City


def get_city_keyboard(
    all_cities: List[City],
    selected_ids: List[int] = None,
    for_post: bool = False
) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для множественного выбора городов (университетов)"""
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()

    # Определяем callback_data в зависимости от контекста
    if for_post:
        prefix = "post_city_"
        select_all_callback = "post_city_select_all"
        confirm_callback = "post_city_confirm"
        cancel_callback = "cancel_post"
    else:
        prefix = "city_"
        select_all_callback = "user_city_select_all"
        confirm_callback = "confirm_cities"
        cancel_callback = "main_menu"  # Для отмены настройки профиля

    # Кнопки городов
    for city in all_cities:
        is_selected = city.id in selected_ids
        checkbox = "⭐️" if is_selected else ""
        text = f"{city.name} {checkbox}".strip()
        builder.button(text=text, callback_data=f"{prefix}{city.id}")

    # Кнопка "Выбрать все"
    all_selected = len(selected_ids) == len(all_cities)
    select_all_text = "Снять все" if all_selected else "Выбрать все"
    builder.button(text=select_all_text, callback_data=select_all_callback)

    builder.adjust(2)

    # Кнопки "Подтвердить" и "Отменить"
    builder.row(
        InlineKeyboardButton(text="Подтвердить ✓", callback_data=confirm_callback)
    )
    if for_post:
        builder.row(
            InlineKeyboardButton(text="Отменить ×", callback_data=cancel_callback)
        )

    return builder.as_markup()
