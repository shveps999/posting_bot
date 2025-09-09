from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_main_keyboard
from events_bot.utils.telegram import safe_edit_message
import os
import random
import logfire

router = Router()

MAIN_MENU_GIF_IDS = [
    os.getenv("MAIN_MENU_GIF_ID_1"),
    os.getenv("MAIN_MENU_GIF_ID_2"),
    os.getenv("MAIN_MENU_GIF_ID_3"),
    os.getenv("MAIN_MENU_GIF_ID_4"),
    os.getenv("MAIN_MENU_GIF_ID_5"),
    os.getenv("MAIN_MENU_GIF_ID_6"),
]

START_GIF_ID = os.getenv("START_GIF_ID")
MAIN_MENU_GIF_IDS = [gif_id for gif_id in MAIN_MENU_GIF_IDS if gif_id]


def register_start_handlers(dp: Router):
    dp.include_router(router)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db):
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    user_cities = await UserService.get_user_cities(db, user.id)
    user_categories = await UserService.get_user_categories(db, user.id)

    if user_cities and user_categories:
        await show_main_menu(message)
        return

    selected_cities = [city.name for city in user_cities] if user_cities else []

    if START_GIF_ID:
        try:
            sent = await message.answer_animation(
                animation=START_GIF_ID,
                caption="✨ Загружаем Сердце...",
                parse_mode="HTML"
            )
            await state.update_data(start_gif_message_id=sent.message_id, selected_cities=selected_cities)
            await show_city_selection(sent, db, selected_cities)
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки START_GIF: {e}")

    await message.answer(
        "Бот поможет быть в курсе актуальных и интересных мероприятий твоего ВУЗа по выбранным категориям интересов. А еще здесь можно создать свое мероприятие. Начнем!\n\n"
        "Для начала выберите ваши университеты:",
        reply_markup=get_city_keyboard(selected_cities=selected_cities),
        parse_mode="HTML"
    )
    await state.set_state(UserStates.waiting_for_cities)
    await state.update_data(selected_cities=selected_cities)


async def show_city_selection(message: Message, db, selected_cities=None):
    """Показать выбор города, отредактировав сообщение с гифкой"""
    try:
        await safe_edit_message(
            message=message,
            text="Для начала выберите ваши университеты:",
            reply_markup=get_city_keyboard(selected_cities=selected_cities or []),
            parse_mode="HTML"
        )
    except Exception as e:
        logfire.error(f"Ошибка при редактировании гифки: {e}")


async def show_main_menu(message: Message):
    if MAIN_MENU_GIF_IDS:
        selected_gif = random.choice(MAIN_MENU_GIF_IDS)
        try:
            await message.answer_animation(
                animation=selected_gif,
                caption="",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки гифки главного меню: {e}")
    await message.answer("Выберите действие:", reply_markup=get_main_keyboard())


@router.message(F.text.in_(["/menu", "/main_menu"]))
async def cmd_main_menu(message: Message):
    await show_main_menu(message)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    await show_main_menu(callback.message)
    await callback.answer()
