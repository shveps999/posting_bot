from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import List
from events_bot.database.models import Category

def get_category_selection_keyboard(
    categories: List[Category], 
    selected_ids: List[int] = None,
    for_post: bool = False
) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора категорий (множественный выбор)"""
    if selected_ids is None:
        selected_ids = []
        
    builder = InlineKeyboardBuilder()
    
    # Префиксы для разных контекстов
    prefix = "post_category_" if for_post else "category_"
    confirm_callback = "post_confirm_categories" if for_post else "confirm_categories"
    
    # Добавляем кнопки для каждой категории
    for category in categories:
        is_selected = category.id in selected_ids
        checkbox = "✅" if is_selected else "❌"
        text = f"{category.name} {checkbox}"
        builder.button(text=text, callback_data=f"{prefix}{category.id}")
        
    # Располагаем по 2 в ряд
    builder.adjust(2)
    
    # Кнопка подтверждения
    builder.row()
    builder.button(text="Подтвердить ✓", callback_data=confirm_callback)
    
    # Для поста добавляем кнопку отмены
    if for_post:
        builder.row()
        builder.button(text="Отменить ×", callback_data="cancel_post")
        
    return builder.as_markup()
