from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_city_keyboard(selected_cities: list = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора нескольких университетов"""
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"
    ]

    if selected_cities is None:
        selected_cities = []

    builder = InlineKeyboardBuilder()

    for city in cities:
        checkbox = "⭐️" if city in selected_cities else ""
        text = f"{city} {checkbox}".strip()
        builder.button(text=text, callback_data=f"city_{city}")

    builder.adjust(2)

    all_selected = len(selected_cities) == len(cities)
    select_all_text = "Выбрать все ⭐️" if all_selected else "Выбрать все"
    builder.button(text=select_all_text, callback_data="select_all_cities")

    builder.row(
        InlineKeyboardBuilder().button(text="Подтвердить ✓", callback_data="confirm_cities").as_markup()
    )

    return builder.as_markup()
