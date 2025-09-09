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
    prefix = "post_city_" if for_post else "city_"

    if for_post:
        # Для создания поста — множественный выбор
        for city in cities:
            is_selected = city in selected_cities
            checkbox = "⭐️" if is_selected else ""
            text = f"{city} {checkbox}".strip()
            builder.button(text=text, callback_data=f"{prefix}{city}")

        # Кнопка "Выбрать все"
        all_selected = len(selected_cities) == len(cities)
        select_all_text = "Выбрать все ⭐️" if all_selected else "Выбрать все"
        builder.button(text=select_all_text, callback_data="post_city_select_all")

        builder.adjust(2)

        # Кнопки "Подтвердить" и "Отменить"
        builder.row(InlineKeyboardButton(text="Подтвердить ✓", callback_data="post_city_confirm"))
        builder.row(InlineKeyboardButton(text="Отменить ×", callback_data="cancel_post"))
    else:
        # Для пользователя — множественный выбор
        for city in cities:
            is_selected = city in selected_cities
            checkbox = "⭐️" if is_selected else ""
            text = f"{city} {checkbox}".strip()
            builder.button(text=text, callback_data=f"{prefix}{city}")

        # Кнопка "Выбрать все"
        all_selected = len(selected_cities) == len(cities)
        select_all_text = "Выбрать все ⭐️" if all_selected else "Выбрать все"
        builder.button(text=select_all_text, callback_data="select_all_cities")

        builder.adjust(2)

        # Кнопка "Подтвердить"
        builder.row(InlineKeyboardButton(text="Подтвердить ✓", callback_data="confirm_cities"))

    return builder.as_markup()
