from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_feed_list_keyboard(
    posts, current_page: int, total_pages: int, start_index: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура списка постов (подборка)"""
    builder = InlineKeyboardBuilder()

    # Кнопки с цифрами — все в одной строке
    for idx, post in enumerate(posts, start=start_index):
        builder.button(
            text=f"{idx}",
            callback_data=f"feed_open_{post.id}_{current_page}_{total_pages}"
        )

    # Навигация (если есть)
    if current_page > 0 or current_page < total_pages - 1:
        if current_page > 0:
            builder.button(
                text="‹ Назад", callback_data=f"feed_prev_{current_page}_{total_pages}"
            )
        if current_page < total_pages - 1:
            builder.button(
                text="Вперед ›", callback_data=f"feed_next_{current_page}_{total_pages}"
            )

    # Кнопка "Главное меню" — всегда на отдельной строке
    builder.button(text="💌 Главное меню", callback_data="main_menu")

    # Располагаем:
    # 1. Все цифры в одной строке
    # 2. Навигация — в следующей строке (если есть)
    # 3. Главное меню — в последней строке
    if current_page > 0 or current_page < total_pages - 1:
        builder.adjust(len(posts), 2, 1)
    else:
        builder.adjust(len(posts), 1)

    return builder.as_markup()


def get_liked_list_keyboard(
    posts, current_page: int, total_pages: int, start_index: int = 1
) -> InlineKeyboardMarkup:
    """Клавиатура списка избранных постов"""
    builder = InlineKeyboardBuilder()

    # Кнопки с цифрами
    for idx, post in enumerate(posts, start=start_index):
        builder.button(
            text=f"{idx}",
            callback_data=f"liked_open_{post.id}_{current_page}_{total_pages}"
        )

    # Навигация
    if current_page > 0 or current_page < total_pages - 1:
        if current_page > 0:
            builder.button(
                text="‹ Назад", callback_data=f"liked_prev_{current_page}_{total_pages}"
            )
        if current_page < total_pages - 1:
            builder.button(
                text="Вперед ›", callback_data=f"liked_next_{current_page}_{total_pages}"
            )

    # Главное меню — всегда внизу
    builder.button(text="💌 Главное меню", callback_data="main_menu")

    # Расположение: как в ленте
    if current_page > 0 or current_page < total_pages - 1:
        builder.adjust(len(posts), 2, 1)
    else:
        builder.adjust(len(posts), 1)

    return builder.as_markup()


def get_feed_post_keyboard(
    current_page: int,
    total_pages: int,
    post_id: int,
    is_liked: bool = False,
    likes_count: int = 0,
    url: str | None = None,
) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра поста в ленте"""
    builder = InlineKeyboardBuilder()
    heart_emoji = "В избранном ❤️" if is_liked else "В избранное 🤍"
    heart_text = f"{heart_emoji} {likes_count}" if likes_count > 0 else heart_emoji

    # Добавляем в нужном порядке
    builder.button(text=heart_text, callback_data=f"feed_heart_{post_id}_{current_page}_{total_pages}")
    
    if url:
        builder.button(text="🔗 Подробнее", url=url)
    
    builder.button(text="‹ К списку", callback_data=f"feed_back_{current_page}_{total_pages}")
    builder.button(text="💌 Главное меню", callback_data="main_menu")

    # Располагаем: максимум по 2 в ряд
    if url:
        builder.adjust(2, 2)  # [лайк][ссылка] [назад][меню]
    else:
        builder.adjust(1, 2)  # [лайк] [назад][меню]

    return builder.as_markup()


def get_liked_post_keyboard(
    current_page: int,
    total_pages: int,
    post_id: int,
    is_liked: bool = False,
    likes_count: int = 0,
) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра поста в избранном"""
    builder = InlineKeyboardBuilder()
    heart_emoji = "В избранном ❤️" if is_liked else "В избранное 🤍"
    heart_text = f"{heart_emoji} {likes_count}" if likes_count > 0 else heart_emoji

    # Порядок: лайк → к списку → главное меню
    builder.button(text=heart_text, callback_data=f"liked_heart_{post_id}_{current_page}_{total_pages}")
    builder.button(text="‹ К списку", callback_data=f"liked_back_{current_page}_{total_pages}")
    builder.button(text="💌 Главное меню", callback_data="main_menu")

    # Располагаем: [лайк] [назад][меню]
    builder.adjust(1, 2)

    return builder.as_markup()
