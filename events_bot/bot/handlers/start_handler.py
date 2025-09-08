from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService
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
    # Удаляем команду
    try:
        await message.delete()
    except Exception:
        pass

    # Регистрируем пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Если уже настроил профиль — главное меню
    if user.city and await UserService.get_user_categories(db, message.from_user.id):
        await show_main_menu(message)
        return

    # Обнуляем Reply-клавиатуру
    await message.answer("Привет!", reply_markup=ReplyKeyboardRemove())

    # Показываем сообщение с выбором города
    await message.answer(
        "👋 Привет! Бот поможет быть в курсе актуальных и интересных мероприятий твоего вуза по выбранным категориям интересов.\n\n"
        "А еще здесь можно создать и разместить свое мероприятие. Начнем!\n\n"
        "Для начала выберите ваш город:",
        reply_markup=get_city_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(UserStates.waiting_for_city)


async def show_city_selection(message: Message, db):
    """Показать выбор города, отредактировав сообщение с гифкой"""
    try:
        await message.edit_caption(
            caption=(
                "👋 Привет! Бот поможет быть в курсе актуальных и интересных мероприятий твоего вуза по выбранным категориям интересов.\n\n"
                "А еще здесь можно создать и разместить свое мероприятие. Начнем!\n\n"
                "Для начала выберите ваш город:"
            ),
            reply_markup=get_city_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logfire.error(f"Ошибка при редактировании гифки: {e}")


async def show_main_menu(message: Message):
    """Отправить главное меню — только гифка без текста"""
    if MAIN_MENU_GIF_IDS:
        selected_gif = random.choice(MAIN_MENU_GIF_IDS)
        try:
            await message.answer_animation(
                animation=selected_gif,
                # Никакого caption — только гифка
                reply_markup=get_main_keyboard()
            )
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки гифки главного меню: {e}")

    # Резерв: если гифок нет — текстовое меню
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
    await show_main_menu(callback.message)
    await callback.answer()
