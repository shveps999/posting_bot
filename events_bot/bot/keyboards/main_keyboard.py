from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с кнопкой избранного"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📮⠀Актуальные мероприятия", callback_data="feed")
    builder.button(text="❤️⠀Мое избранное⠀⠀⠀⠀⠀⠀⠀", callback_data="liked_posts")
    builder.button(text="📝    Создать мероприятие⠀⠀         ", callback_data="create_post") 
    builder.button(text="⭐️⠀ Изменить категории⠀⠀⠀", callback_data="change_category")
    builder.button(text="🎓    Изменить университет⠀ ", callback_data="change_city")
    builder.button(text="💬⠀Помощь                   ", callback_data="help")
    
    builder.adjust(1)
    return builder.as_markup()
