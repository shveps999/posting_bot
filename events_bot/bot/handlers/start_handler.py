from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CityService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_main_keyboard
import os
import random
import logfire

router = Router()

# Получаем file_id гифок из переменных окружения
MAIN_MENU_GIF_IDS = [
    os.getenv("MAIN_MENU_GIF_ID_1"),
    os.getenv("MAIN_MENU_GIF_ID_2"),
    os.getenv("MAIN_MENU_GIF_ID_3"),
    os.getenv("MAIN_MENU_GIF_ID_4"),
    os.getenv("MAIN_MENU_GIF_ID_5"),
    os.getenv("MAIN_MENU_GIF_ID_6"),
]

# Гифка при старте
START_GIF_ID = os.getenv("START_GIF_ID")

# Очистка: убираем None
MAIN_MENU_GIF_IDS = [gif_id for gif_id in MAIN_MENU_GIF_IDS if gif_id]


def register_start_handlers(dp: Router):
    """Регистрация обработчиков команды start"""
    dp.include_router(router)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db):
    """Обработчик команды /start"""
    # 1. Удаляем команду /start, отправленную пользователем
    try:
        await message.delete()
    except Exception:
        pass

    # 2. Отправляем приветственное сообщение, которое остается в чате
    await message.answer("👋 Добро пожаловать в Сердце!")

    # 3. Регистрируем пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # 4. Если пользователь уже настроил профиль — показываем главное меню
    user_cities = await UserService.get_user_cities(db, message.from_user.id)
    user_categories = await UserService.get_user_categories(db, message.from_user.id)
    if user_cities and user_categories:
        await show_main_menu(message)
        return

    # 5. Показываем выбор города (это будет новое, отдельное сообщение)
    if START_GIF_ID:
        try:
            sent_message = await message.answer_animation(
                animation=START_GIF_ID
            )
            await show_city_selection(sent_message, state, db, user_id=message.from_user.id)
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки START_GIF: {e}")

    # Резервный вариант без гифки
    await show_city_selection(message, state, db, user_id=message.from_user.id, is_text_based=True)


async def show_city_selection(message: Message, state: FSMContext, db, user_id: int, is_text_based: bool = False):
    """Показать выбор города, отредактировав сообщение с гифкой или отправив новое"""
    all_cities = await CityService.get_all_cities(db)
    user_cities = await UserService.get_user_cities(db, user_id)
    selected_ids = [c.id for c in user_cities]

    text = (
        "Бот поможет всегда быть в курсе актуальных мероприятий твоего университета по выбранным категориям интересов. А еще здесь можно создать и разместить свое мероприятие. Начнем!\n\n"
        "Для начала выберите инетересующие университеты:"
    )
    keyboard = get_city_keyboard(all_cities, selected_ids)
    
    if is_text_based:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Редактируем подпись к уже отправленной гифке
        await message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    
    await state.set_state(UserStates.waiting_for_city)


async def show_main_menu(message: Message):
    """Отправить главное меню — гифка с подписью и кнопками"""
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

    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text.in_(["/menu", "/main_menu"]))
async def cmd_main_menu(message: Message):
    """Обработчик команды /menu"""
    await show_main_menu(message)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик кнопки «🏠 Главное меню»"""
    try:
        await callback.message.delete()
    except Exception:
        pass
    await show_main_menu(callback.message)
    await callback.answer()
