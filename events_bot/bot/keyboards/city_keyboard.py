from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_keyboard(for_post: bool = False, selected_cities: list = None) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора городов (университетов)"""
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"
    ]
    
    if selected_cities is None:
        selected_cities = []
    
    builder = InlineKeyboardBuilder()
    
    # Используем разные префиксы для разных контекстов
    prefix = "post_city_" if for_post else "city_"
    
    if for_post:
        # Добавляем все города с чекбоксами
        for city in cities:
            is_selected = city in selected_cities
            checkbox = "⭐️" if is_selected else ""
            text = f"{city} {checkbox}".strip()
            builder.button(text=text, callback_data=f"{prefix}{city}")
        
        # Кнопка "Выбрать все" — сразу после городов, как последняя в списке
        all_selected = len(selected_cities) == len(cities)
        select_all_text = f"Выбрать все ⭐️" if all_selected else "Выбрать все"
        builder.button(
            text=select_all_text,
            callback_data="post_city_select_all"
        )
        
        # Располагаем все кнопки (города + "Выбрать все") по 2 в ряд
        builder.adjust(2)
        
        # Кнопки "Подтвердить" и "Отменить" — всегда видны, каждая на своей строке
        builder.row(
            InlineKeyboardButton(
                text="Подтвердить ✓", 
                callback_data="post_city_confirm"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="Отменить ×", 
                callback_data="cancel_post"
            )
        )
    else:
        # Для выбора города пользователя (одиночный выбор)
        for city in cities:
            builder.button(text=city, callback_data=f"{prefix}{city}")
        builder.adjust(2)
    
    return builder.as_markup()
