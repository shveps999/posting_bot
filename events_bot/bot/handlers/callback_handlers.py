from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_category_selection_keyboard, get_main_keyboard

router = Router()


def register_callback_handlers(dp: Router):
    """Регистрация обработчиков callback"""
    dp.include_router(router)


@router.callback_query(F.data.startswith("category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext, db):
    """Обработка выбора категории (множественный выбор)"""
    category_id = int(callback.data.split("_")[1])

    # Получаем все категории
    categories = await CategoryService.get_all_categories(db)

    # Получаем текущие выбранные категории
    data = await state.get_data()
    selected_ids = data.get("selected_categories", [])

    # Добавляем или удаляем категорию из выбранных
    if category_id in selected_ids:
        selected_ids.remove(category_id)
    else:
        selected_ids.append(category_id)

    await state.update_data(selected_categories=selected_ids)

    # Обновляем клавиатуру (меняем только кнопки — безопасно)
    await callback.message.edit_reply_markup(
        reply_markup=get_category_selection_keyboard(categories, selected_ids)
    )
    await callback.answer()


async def safe_edit_message(message: Message, text: str, reply_markup=None, parse_mode=None):
    """Безопасное редактирование сообщения: поддерживает текст и подпись"""
    try:
        if message.text:
            await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif message.caption:
            await message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await message.edit_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        if "message is not modified" in str(e):
            pass  # Игнорируем
        else:
            raise


@router.callback_query(F.data == "confirm_categories")
async def confirm_categories_selection(callback: CallbackQuery, state: FSMContext, db):
    """Подтверждение выбора категорий"""
    data = await state.get_data()
    selected_ids = data.get("selected_categories", [])

    if not selected_ids:
        await callback.answer("❌ Выберите хотя бы одну категорию!")
        return

    # Сохраняем выбранные категории пользователю
    await UserService.select_categories(db, callback.from_user.id, selected_ids)

    # Получаем названия выбранных категорий
    categories = await CategoryService.get_all_categories(db)
    selected_categories = [cat for cat in categories if cat.id in selected_ids]
    category_names = ", ".join([cat.name for cat in selected_categories])

    # Редактируем сообщение с подтверждением
    await safe_edit_message(
        callback.message,
        text=f"✅ Выбраны категории: {category_names}\n\n"
             "Теперь вы можете создавать посты в этих категориях.",
        reply_markup=None
    )

    # Переход к главному меню
    await safe_edit_message(
        callback.message,
        text="Выберите действие:",
        reply_markup=get_main_keyboard()
    )

    await state.clear()
    await callback.answer()
