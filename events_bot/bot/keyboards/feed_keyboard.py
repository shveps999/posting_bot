from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_feed_list_keyboard(
    posts, current_page: int, total_pages: int, start_index: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура списка постов (подборка)"""
    builder = InlineKeyboardBuilder()
    for idx, post in enumerate(posts, start=start_index):
        builder.button(
            text=f"{idx}",  # Только номер
            callback_data=f"feed_open_{post.id}_{current_page}_{total_pages}"
        )
    # Навигация
    if current_page > 0:
        builder.button(
            text="⬅️ Назад", callback_data=f"feed_prev_{current_page}_{total_pages}"
        )
    if current_page < total_pages - 1:
        builder.button(
            text="Вперед ➡️", callback_data=f"feed_next_{current_page}_{total_pages}"
        )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)  # Каждая кнопка — на отдельной строке
    return builder.as_markup()


def get_feed_post_keyboard(
    current_page: int,
    total_pages: int,
    post_id: int,
    is_liked: bool = False,
    likes_count: int = 0,
    url: str | None = None,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки одного поста"""
    builder = InlineKeyboardBuilder()
    heart_emoji = "❤️" if is_liked else "🤍"
    heart_text = f"{heart_emoji} {likes_count}" if likes_count > 0 else heart_emoji
    builder.button(
        text=heart_text,
        callback_data=f"feed_heart_{post_id}_{current_page}_{total_pages}",
    )
    builder.button(
        text="↩️ К списку", callback_data=f"feed_back_{current_page}_{total_pages}"
    )
    # Навигация
    if current_page > 0:
        builder.button(
            text="⬅️ Назад", callback_data=f"feed_prev_{current_page}_{total_pages}"
        )
    if current_page < total_pages - 1:
        builder.button(
            text="Вперед ➡️", callback_data=f"feed_next_{current_page}_{total_pages}"
        )
    if url:
        builder.button(text="🔗 Подробнее", url=url)
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_liked_list_keyboard(
    posts, current_page: int, total_pages: int, start_index: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура списка избранных постов"""
    builder = InlineKeyboardBuilder()
    for idx, post in enumerate(posts, start=start_index):
        builder.button(
            text=f"{idx}",  # Только номер
            callback_data=f"liked_open_{post.id}_{current_page}_{total_pages}"
        )
    if current_page > 0:
        builder.button(
            text="⬅️ Назад", callback_data=f"liked_prev_{current_page}_{total_pages}"
        )
    if current_page < total_pages - 1:
        builder.button(
            text="Вперед ➡️", callback_data=f"liked_next_{current_page}_{total_pages}"
        )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_liked_post_keyboard(
    current_page: int,
    total_pages: int,
    post_id: int,
    is_liked: bool = False,
    likes_count: int = 0,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    heart_emoji = "❤️" if is_liked else "🤍"
    heart_text = f"{heart_emoji} {likes_count}" if likes_count > 0 else heart_emoji
    builder.button(
        text=heart_text,
        callback_data=f"liked_heart_{post_id}_{current_page}_{total_pages}",
    )
    builder.button(
        text="↩️ К списку", callback_data=f"liked_back_{current_page}_{total_pages}"
    )
    if current_page > 0:
        builder.button(
            text="⬅️ Назад", callback_data=f"liked_prev_{current_page}_{total_pages}"
        )
    if current_page < total_pages - 1:
        builder.button(
            text="Вперед ➡️", callback_data=f"liked_next_{current_page}_{total_pages}"
        )
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(2, 2)
    return builder.as_markup()
