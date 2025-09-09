from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import PostService, UserService
from events_bot.bot.states import PostStates
from events_bot.bot.keyboards import (
    get_main_keyboard,
    get_city_keyboard,
    get_category_selection_keyboard,
    get_skip_image_keyboard,
)
import logfire
from datetime import datetime
from events_bot.bot.keyboards.notification_keyboard import get_post_notification_keyboard
from events_bot.storage import file_storage

router = Router()

def register_post_handlers(dp: Router):
    """Регистрация обработчиков создания поста"""
    dp.include_router(router)

@router.message(F.text == "✏️ Создать мероприятие")
async def cmd_create_post(message: Message, state: FSMContext):
    """Начало создания поста"""
    logfire.info(f"Пользователь {message.from_user.id} начал создание поста")
    await message.answer(
        "Выберите города, где будет проходить мероприятие:", 
        reply_markup=get_city_keyboard(for_post=True)
    )
    await state.set_state(PostStates.waiting_for_city_selection)

@router.callback_query(F.data.startswith("post_city_"))
async def process_post_city_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города для поста"""
    city = callback.data[10:]  # Убираем префикс "post_city_"
    
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
        reply_markup=get_city_keyboard(for_post=True, selected_cities=selected_cities)
    )
    
    await callback.answer()

@router.callback_query(F.data == "post_city_select_all")
async def select_all_post_cities(callback: CallbackQuery, state: FSMContext):
    """Выбрать все города для поста"""
    cities = [
        "УрФУ", "УГМУ", "УрГЭУ", "УрГПУ",
        "УрГЮУ", "УГГУ", "УрГУПС", "УрГАХУ",
        "УрГАУ", "РГППУ", "РАНХиГС"
    ]
    
    await state.update_data(selected_cities=cities)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(for_post=True, selected_cities=cities)
    )
    
    await callback.answer()

@router.callback_query(F.data == "post_city_confirm")
async def confirm_post_cities(callback: CallbackQuery, state: FSMContext):
    """Подтвердить выбор городов для поста"""
    data = await state.get_data()
    selected_cities = data.get("selected_cities", [])
    
    if not selected_cities:
        await callback.answer("❌ Выберите хотя бы один город!")
        return
    
    await state.update_data(selected_cities=selected_cities)
    
    # Переходим к выбору категорий
    from events_bot.database.services import CategoryService
    
    # Получаем db из data
    db = callback.bot.get("db")
    if not db:
        await callback.answer("❌ Ошибка: нет подключения к базе данных")
        return
        
    categories = await CategoryService.get_all_categories(db)
    
    try:
        await callback.message.delete()
        await callback.message.answer(
            f"📍 Выбраны города: {', '.join(selected_cities)}\n"
            "Теперь выберите категории мероприятия:",
            reply_markup=get_category_selection_keyboard(categories, for_post=True),
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    
    await state.set_state(PostStates.waiting_for_category_selection)
    await callback.answer()

@router.callback_query(F.data.startswith("post_category_"))
async def process_post_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории для поста"""
    category_id = int(callback.data.split("_")[2])  # post_category_{id}
    
    # Получаем db из callback.bot
    db = callback.bot.get("db")
    if not db:
        await callback.answer("❌ Ошибка: нет подключения к базе данных")
        return
    
    # Получаем все категории
    from events_bot.database.services import CategoryService
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
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_category_selection_keyboard(categories, selected_ids, for_post=True)
    )
    
    await callback.answer()

@router.callback_query(F.data == "post_confirm_categories")
async def confirm_post_categories(callback: CallbackQuery, state: FSMContext):
    """Подтвердить выбор категорий для поста"""
    data = await state.get_data()
    selected_ids = data.get("selected_categories", [])
    
    if not selected_ids:
        await callback.answer("❌ Выберите хотя бы одну категорию!")
        return
    
    await state.update_data(selected_categories=selected_ids)
    
    try:
        await callback.message.delete()
        await callback.message.answer(
            "📝 Введите заголовок мероприятия (до 100 символов):"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    
    await state.set_state(PostStates.waiting_for_title)
    await callback.answer()

@router.message(PostStates.waiting_for_title)
async def process_post_title(message: Message, state: FSMContext):
    """Обработка заголовка поста"""
    title = message.text.strip()
    
    if len(title) > 100:
        await message.answer("❌ Заголовок не должен превышать 100 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(title=title)
    
    await message.answer(
        "📄 Введите описание мероприятия (до 2000 символов):\n"
        "Вы можете использовать следующие элементы форматирования:\n"
        "• <b>жирный текст</b>\n"
        "• <i>курсив</i>\n"
        "• <u>подчеркнутый</u>\n"
        "• <s>зачеркнутый</s>",
        parse_mode="HTML"
    )
    
    await state.set_state(PostStates.waiting_for_content)

@router.message(PostStates.waiting_for_content)
async def process_post_content(message: Message, state: FSMContext):
    """Обработка содержания поста"""
    content = message.text.strip()
    
    if len(content) > 2000:
        await message.answer("❌ Описание не должно превышать 2000 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(content=content)
    
    await message.answer(
        "📎 Хотите добавить изображение к мероприятию?",
        reply_markup=get_skip_image_keyboard()
    )
    
    await state.set_state(PostStates.waiting_for_image)

@router.callback_query(F.data == "skip_image")
async def skip_image(callback: CallbackQuery, state: FSMContext):
    """Пропустить добавление изображения"""
    try:
        await callback.message.delete()
        await callback.message.answer(
            "📍 Введите адрес проведения мероприятия (необязательно):"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    
    await state.set_state(PostStates.waiting_for_address)
    await callback.answer()

@router.message(PostStates.waiting_for_image)
async def process_post_image(message: Message, state: FSMContext):
    """Обработка изображения поста"""
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте изображение или нажмите 'Пропустить'")
        return
    
    # Сохраняем file_id фото
    photo = message.photo[-1]  # Берем фото самого высокого качества
    await state.update_data(image_id=photo.file_id)
    
    await message.answer(
        "📍 Введите адрес проведения мероприятия (необязательно):"
    )
    
    await state.set_state(PostStates.waiting_for_address)

@router.message(PostStates.waiting_for_address)
async def process_post_address(message: Message, state: FSMContext):
    """Обработка адреса поста"""
    address = message.text.strip()
    
    if address.lower() == "/skip":
        address = None
    elif len(address) > 500:
        await message.answer("❌ Адрес не должен превышать 500 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(address=address)
    
    await message.answer(
        "🌐 Введите ссылку на мероприятие (необязательно):\n"
        "Например: https://example.com"
    )
    
    await state.set_state(PostStates.waiting_for_url)

@router.message(PostStates.waiting_for_url)
async def process_post_url(message: Message, state: FSMContext):
    """Обработка URL поста"""
    url = message.text.strip()
    
    if url.lower() == "/skip":
        url = None
    elif not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ Ссылка должна начинаться с http:// или https:// Попробуйте еще раз:")
        return
    elif len(url) > 500:
        await message.answer("❌ Ссылка не должна превышать 500 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(url=url)
    
    await message.answer(
        "📅 Введите дату и время проведения мероприятия в формате ДД.ММ.ГГГГ ЧЧ:ММ (необязательно):\n"
        "Например: 25.12.2024 15:30"
    )
    
    await state.set_state(PostStates.waiting_for_event_datetime)

@router.message(PostStates.waiting_for_event_datetime)
async def process_post_event_datetime(message: Message, state: FSMContext, db):
    """Обработка даты и времени поста"""
    event_at_str = message.text.strip()
    event_at = None
    
    if event_at_str.lower() != "/skip":
        try:
            event_at = datetime.strptime(event_at_str, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ\n"
                "Например: 25.12.2024 15:30\n"
                "Или отправьте /skip чтобы пропустить"
            )
            return
    
    # Получаем все данные
    data = await state.get_data()
    
    # Создаем пост
    post = await PostService.create_post(
        db=db,
        title=data["title"],
        content=data["content"],
        author_id=message.from_user.id,
        category_ids=data["selected_categories"],
        cities=data["selected_cities"],
        image_id=data.get("image_id"),
        event_at=event_at,
        url=data.get("url"),
        address=data.get("address"),
    )
    
    await message.answer(
        "✅ Мероприятие отправлено на модерацию!\n"
        "После одобрения вы получите уведомление.",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()

@router.callback_query(F.data == "cancel_post")
async def cancel_post_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания поста"""
    await state.clear()
    
    try:
        await callback.message.delete()
        await callback.message.answer(
            "❌ Создание мероприятия отменено",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()
