from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
import json

def get_city_keyboard(
    for_post: bool = False, 
    selected_cities: Optional[List[str]] = None,
    for_user: bool = False  # Новый параметр для выбора города пользователя
) -> InlineKeyboardMarkup:
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
    if for_post:
        prefix = "post_city_"
    elif for_user:
        prefix = "user_city_"
    else:
        prefix = "city_"
    
    if for_post or for_user:
        # Добавляем все города с чекбоксами
        for city in cities:
            is_selected = city in selected_cities
            checkbox = "⭐️" if is_selected else ""
            text = f"{city} {checkbox}".strip()
            builder.button(text=text, callback_data=f"{prefix}{city}")
            
        # Кнопка "Выбрать все" — сразу после городов
        all_selected = len(selected_cities) == len(cities)
        select_all_text = "Выбрать все ⭐️" if all_selected else "Выбрать все"
        
        if for_post:
            builder.button(
                text=select_all_text,
                callback_data="post_city_select_all"
            )
        elif for_user:
            builder.button(
                text=select_all_text,
                callback_data="user_city_select_all"
            )
            
        # Располагаем все кнопки (города + "Выбрать все") по 2 в ряд
        builder.adjust(2)
        
        # Кнопки "Подтвердить" и "Отменить" — всегда видны
        if for_post:
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
        elif for_user:
            builder.row(
                InlineKeyboardButton(
                    text="Подтвердить ✓", 
                    callback_data="user_city_confirm"
                )
            )
    else:
        # Для выбора города пользователя (одиночный выбор) - старое поведение
        for city in cities:
            builder.button(text=city, callback_data=f"{prefix}{city}")
        builder.adjust(2)
        
    return builder.as_markup()
