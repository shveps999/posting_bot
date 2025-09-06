from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_main_keyboard
import os
import random

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

# Очистка: убираем None (если какая-то переменная не задана)
MAIN_MENU_GIF_IDS = [gif_id for gif_id in MAIN_MENU_GIF_IDS if gif_id]


def register_start_handlers(dp: Router):
    """Регистрация обработчиков команды start"""
    dp.include_router(router)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db):
    """Обработчик команды /start"""
    # Регистрируем пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Проверяем, есть ли у пользователя город
    if not user.city:
        await message.answer(
            "👋 Добро пожаловать в Сердце! Бот поможет быть в курсе актуальных и интересных мероприятий твоего города по выбранным категориям интересов. А еще здесь можно создать свое мероприятие. Начнем!\n\n"
            "Для начала выберите ваш город:",
            reply_markup=get_city_keyboard(),
        )
        # Отправляем гифку после приветствия
        if START_GIF_ID:
            try:
                await message.answer_animation(animation=START_GIF_ID)
            except Exception as e:
                print(f"Ошибка отправки гифки /start: {e}")
        await state.set_state(UserStates.waiting_for_city)
    else:
        # Отправляем гифку при повторном входе
        if START_GIF_ID:
            try:
                await message.answer_animation(animation=START_GIF_ID)
            except Exception as e:
                print(f"Ошибка отправки гифки /start: {e}")
        await show_main_menu(message)


@router.message(F.text.in_(["/menu", "/main_menu"]))
async def cmd_main_menu(message: Message):
    """Обработчик команды /menu — показать главное меню с рандомной гифкой"""
    await show_main_menu(message)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик кнопки «🏠 Главное меню»"""
    await show_main_menu(callback.message)
    await callback.answer()  # Убираем "часики" у кнопки


async def show_main_menu(message: Message):
    """Отправить главное меню с одной из 7 гифок (случайно)"""
    user = message.from_user
    welcome_text = f"👋 Привет, {user.first_name or user.username or 'друг'}!\n\n"
    welcome_text += "Выберите действие:"

    # Если есть хотя бы одна гифка — выбираем случайную
    if MAIN_MENU_GIF_IDS:
        selected_gif = random.choice(MAIN_MENU_GIF_IDS)
        try:
            await message.answer_animation(
                animation=selected_gif,
                reply_markup=get_main_keyboard()
            )
            return
        except Exception as e:
            print(f"Ошибка отправки гифки: {e}")

    # Если гифок нет или ошибка — отправляем текстовое меню
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
