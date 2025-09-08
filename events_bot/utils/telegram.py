from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
import logfire


async def safe_edit_message(message: Message, text: str, reply_markup=None, parse_mode=None):
    """
    Безопасно редактирует сообщение: использует edit_text или edit_caption в зависимости от типа
    """
    try:
        if message.text:
            await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif message.caption:
            await message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            # Если нет ни text, ни caption — не редактируем
            pass
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass  # Игнорируем
        elif "message to edit not found" in str(e):
            pass  # Сообщение удалено
        else:
            logfire.error(f"TelegramBadRequest при редактировании сообщения: {e}")
    except Exception as e:
        logfire.error(f"Ошибка при редактировании сообщения: {e}")
