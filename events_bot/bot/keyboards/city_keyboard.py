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
    
    if not for_post:
        builder.row(
            InlineKeyboardButton(
                text="Подтвердить ✓", 
                callback_data="confirm_cities"
            )
        )
    
    return builder.as_markup()
