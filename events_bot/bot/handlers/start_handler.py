from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_main_keyboard
import os

router = Router()

# Получаем file_id гифки из переменных окружения
MAIN_MENU_GIF_ID = os.getenv("MAIN_MENU_GIF_ID")


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
        await state.set_state(UserStates.waiting_for_city)
    else:
        await show_main_menu(message)


@router.message(F.text.in_(["/menu", "/main_menu"]))
async def cmd_main_menu(message: Message):
    """Обработчик команды /menu — показать главное меню с гифкой"""
    await show_main_menu(message)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик кнопки «🏠 Главное меню»"""
    await show_main_menu(callback.message)
    await callback.answer()  # Убираем "часики" у кнопки


async def show_main_menu(message: Message):
    """Отправить главное меню с гифкой (если есть)"""
    user = message.from_user
    welcome_text = f"👋 Привет, {user.first_name or user.username or 'друг'}!\n\n"
    welcome_text += "Выберите действие:"

    # Если есть гифка — отправляем с анимацией
    if MAIN_MENU_GIF_ID:
        try:
            await message.answer_animation(
                animation=MAIN_MENU_GIF_ID,
                caption=welcome_text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return
        except Exception as e:
            # Если гифка не загрузилась — логируем и отправляем просто текст
            print(f"Ошибка отправки гифки: {e}")

    # Если гифки нет или ошибка — отправляем обычное сообщение
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
