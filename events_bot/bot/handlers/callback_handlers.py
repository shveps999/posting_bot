from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_category_selection_keyboard, get_main_keyboard
from events_bot.bot.handlers.start_handler import MAIN_MENU_GIF_IDS
import random
import logfire

router = Router()


def register_callback_handlers(dp: Router):
    dp.include_router(router)


@router.callback_query(F.data.startswith("category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext, db):
    category_id = int(callback.data.split("_")[1])
    categories = await CategoryService.get_all_categories(db)
    data = await state.get_data()
    selected_ids = data.get("selected_categories", [])

    if category_id in selected_ids:
        selected_ids.remove(category_id)
    else:
        selected_ids.append(category_id)

    await state.update_data(selected_categories=selected_ids)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_category_selection_keyboard(categories, selected_ids)
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data == "confirm_categories")
async def confirm_categories_selection(callback: CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    selected_ids = data.get("selected_categories", [])

    if not selected_ids:
        await callback.answer("❌ Выберите хотя бы одну категорию!")
        return

    await UserService.select_categories(db, callback.from_user.id, selected_ids)

    try:
        await callback.message.delete()
    except Exception as e:
        logfire.warning(f"Не удалось удалить сообщение: {e}")

    if MAIN_MENU_GIF_IDS:
        selected_gif = random.choice(MAIN_MENU_GIF_IDS)
        try:
            await callback.message.answer_animation(
                animation=selected_gif,
                caption="",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки гифки: {e}")

    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    await state.clear()
    await callback.answer()
