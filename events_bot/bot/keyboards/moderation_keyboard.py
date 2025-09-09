from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_moderation_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для модерации одного поста"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"moderate_approve_{post_id}")
    builder.button(text="❌ Отклонить", callback_data=f"moderate_reject_{post_id}")
    builder.button(text="✏️ Запросить изменения", callback_data=f"moderate_request_changes_{post_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_moderation_queue_keyboard(posts: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура для очереди модерации"""
    builder = InlineKeyboardBuilder()

    for post in posts:
        builder.button(
            text=f"📄 {post.title[:30]}...",
            callback_data=f"moderate_post_{post.id}"
        )
    builder.adjust(1)

    # Кнопки навигации
    if total_pages > 1:
        if page > 0:
            builder.row()
            builder.button(text="⬅️ Назад", callback_data="moderate_prev_page")
        if page < total_pages - 1:
            builder.button(text="Вперед ➡️", callback_data="moderate_next_page")

    return builder.as_markup()
