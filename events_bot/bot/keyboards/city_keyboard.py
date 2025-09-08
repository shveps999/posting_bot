from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_keyboard(for_post: bool = False, selected_cities: list = None) -> InlineKeyboardMarkup:
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"
    ]
    
    if selected_cities is None:
        selected_cities = []
    
    builder = InlineKeyboardBuilder()
    prefix = "post_city_" if for_post else "city_"
    
    for city in cities:
        is_selected = city in selected_cities
        checkbox = "⭐️" if is_selected else "▫️"
        text = f"{city} {checkbox}"
        builder.button(text=text, callback_data=f"{prefix}{city}")
    
    builder.adjust(2)
    
    # Всегда добавляем "Подтвердить", даже для постов
    buttons = [
        InlineKeyboardButton(text="Подтвердить ✓", callback_data="confirm_post_cities")
    ]
    
    # Если это для поста — добавляем "Отмена"
    if for_post:
        buttons.append(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post"))
    
    builder.row(*buttons)
    
    return builder.as_markup()
