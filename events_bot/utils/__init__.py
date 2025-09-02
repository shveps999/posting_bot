"""
Утилиты для бота
"""

from .category_utils import (
    remove_emoji_from_category,
    get_clean_category_names,
    get_clean_category_string,
    visual_len,
)

__all__ = [
    "remove_emoji_from_category",
    "get_clean_category_names",
    "get_clean_category_string",
    "visual_len",
]
