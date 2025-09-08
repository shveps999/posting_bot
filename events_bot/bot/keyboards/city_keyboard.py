from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_keyboard(for_post: bool = False, selected_cities: list = None) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора городов"""
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"]
    
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
        
        builder.adjust(3)
        
        # Добавляем специальные кнопки для постов
        special_buttons = []
        
        # Кнопка "Выбрать все города"
        special_buttons.append(
            InlineKeyboardButton(
                text="🌍 Выбрать все города", 
                callback_data="post_city_select_all"
            )
        )
        
        # Кнопка подтверждения (только если есть выбранные города)
        if selected_cities:
            special_buttons.append(
                InlineKeyboardButton(
                    text="✅ Подтвердить", 
                    callback_data="post_city_confirm"
                )
            )
        
        # Кнопка отмены
        special_buttons.append(
            InlineKeyboardButton(
                text="❌ Отмена", 
                callback_data="cancel_post"
            )
        )
        
        builder.row(*special_buttons)
    else:
        # Для выбора города пользователя (одиночный выбор)
        for city in cities:
            builder.button(text=city, callback_data=f"{prefix}{city}")
        builder.adjust(2)
    
    return builder.as_markup()
