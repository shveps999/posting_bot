"""
Утилиты для работы с категориями
"""

import re


def remove_emoji_from_category(category_name: str) -> str:
    """Удаляет эмодзи из начала названия категории для чистого текста"""
    # Удаляем эмодзи и пробелы в начале строки
    return re.sub(
        r"^[\U0001F000-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+\s*",
        "",
        category_name,
    )


def get_clean_category_names(categories) -> list:
    """Возвращает список названий категорий без эмодзи"""
    if not categories:
        return ["Неизвестно"]

    return [
        remove_emoji_from_category(getattr(cat, "name", "Неизвестно"))
        for cat in categories
    ]


def get_clean_category_string(categories) -> str:
    """Возвращает строку с названиями категорий без эмодзи, разделенными запятыми"""
    category_names = get_clean_category_names(categories)
    return ", ".join(category_names) if category_names else "Неизвестно"


def visual_len(text: str) -> int:
    """Возвращает визуальную длину текста без учета эмодзи"""
    # Убираем эмодзи для подсчета визуальной длины
    clean_text = re.sub(
        r"[\U0001F000-\U0001F9FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+",
        "",
        text,
    )
    return len(clean_text)
