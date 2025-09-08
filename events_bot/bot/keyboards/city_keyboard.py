from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_keyboard(for_post: bool = False, selected_cities: list = None) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора городов"""
    cities = ["Москва", "Санкт-Петербург"]
    
    if selected_cities is None:
        selected_cities = []
    
    builder = InlineKeyboardBuilder()
    
    # Используем разные префиксы для разных контекстов
    prefix = "post_city_" if for_post else "city_"
    
    if for_post:
        # Кнопки с чекбоксами
        for city in cities:
            is_selected = city in selected_cities
            checkbox = "⭐️" if is_selected else ""
            text = f"{city} {checkbox}"
            builder.button(text=text, callback_data=f"{prefix}{city}")
        
        builder.adjust(1)
        
        # Кнопки "Отмена" и "Подтвердить"
        builder.row(
            InlineKeyboardButton(text="Отменить ×", callback_data="cancel_post"),
            InlineKeyboardButton(text="Подтвердить ✓", callback_data="post_city_confirm")
        )
    else:
        # Обычный выбор города
        for city in cities:
            builder.button(text=city, callback_data=f"{prefix}{city}")
        builder.adjust(1)

    return builder.as_markup()
