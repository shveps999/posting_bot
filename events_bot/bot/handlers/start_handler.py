from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_city_keyboard, get_category_selection_keyboard
import logfire

router = Router()

def register_start_handlers(dp: Router):
    """Регистрация обработчиков стартового экрана"""
    dp.include_router(router)

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, db):
    """Обработчик команды /start"""
    logfire.info(f"Пользователь {message.from_user.id} начал работу с ботом")
    
    # Регистрируем пользователя
    user = await UserService.register_user(
        db=db,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    
    # Проверяем, есть ли у пользователя уже выбранные города
    user_cities = await UserService.get_user_cities(db, message.from_user.id)
    
    if user_cities:
        # Если города уже выбраны, переходим к выбору категорий
        categories = await CategoryService.get_all_categories(db)
        await message.answer(
            "👋 Добро пожаловать в Сердце Екатеринбурга!
"
            "Теперь выберите категории интересов для кастомизации уведомлений и подборки:",
            reply_markup=get_category_selection_keyboard(categories),
        )
        await state.set_state(UserStates.waiting_for_categories)
    else:
        # Если городов нет, предлагаем выбрать города
        await message.answer(
            "👋 Добро пожаловать в Сердце Екатеринбурга!
"
            "Выберите города для получения уведомлений и подборки:",
            reply_markup=get_city_keyboard(for_user=True)
        )
        await state.set_state(UserStates.waiting_for_cities)

@router.callback_query(F.data.startswith("user_city_"))
async def process_user_city_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города пользователя"""
    city = callback.data[10:]  # Убираем префикс "user_city_"
    
    # Получаем текущие выбранные города
    data = await state.get_data()
    selected_cities = data.get("selected_cities", [])
    
    # Добавляем или удаляем город из выбранных
    if city in selected_cities:
        selected_cities.remove(city)
    else:
        selected_cities.append(city)
        
    await state.update_data(selected_cities=selected_cities)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(for_user=True, selected_cities=selected_cities)
    )
    
    await callback.answer()

@router.callback_query(F.data == "user_city_select_all")
async def select_all_user_cities(callback: CallbackQuery, state: FSMContext):
    """Выбрать все города для пользователя"""
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"
    ]
    
    await state.update_data(selected_cities=cities)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(for_user=True, selected_cities=cities)
    )
    
    await callback.answer()

@router.callback_query(F.data == "user_city_confirm")
async def confirm_user_cities(callback: CallbackQuery, state: FSMContext, db):
    """Подтвердить выбор городов пользователя"""
    data = await state.get_data()
    selected_cities = data.get("selected_cities", [])
    
    if not selected_cities:
        await callback.answer("❌ Выберите хотя бы один город!")
        return
    
    # Сохраняем выбранные города
    await UserService.update_user_cities(db, callback.from_user.id, selected_cities)
    
    # Переходим к выбору категорий
    categories = await CategoryService.get_all_categories(db)
    try:
        await callback.message.delete()
        await callback.message.answer(
            f"📍 Города {', '.join(selected_cities)} выбраны!
"
            "Теперь выберите категории интересов для кастомизации уведомлений и подборки:",
            reply_markup=get_category_selection_keyboard(categories),
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()
