from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from typing import Union
import logfire
from sqlalchemy import select
from events_bot.database.services import PostService, CategoryService, CityService
from events_bot.database.models import Category
from events_bot.bot.states import PostStates
from events_bot.bot.keyboards import (
    get_main_keyboard,
    get_category_selection_keyboard,
    get_city_keyboard,
)
from events_bot.storage import file_storage
from loguru import logger
from datetime import timezone
from events_bot.bot.handlers.start_handler import MAIN_MENU_GIF_IDS
import random

router = Router()

# Максимальная длина описания поста (ограничение Telegram для caption)
MAX_CONTENT_LENGTH = 800

def register_post_handlers(dp: Router):
    """Регистрация обработчиков постов"""
    dp.include_router(router)


@router.message(F.text == "/create_post")
async def cmd_create_post(message: Message, state: FSMContext, db):
    """Обработчик команды /create_post"""
    await state.set_state(PostStates.creating_post)
    all_cities = await CityService.get_all_cities(db)
    await message.answer(
        "🎓 Выберите университет(ы) для мероприятия:",
        reply_markup=get_city_keyboard(all_cities, for_post=True)
    )
    await state.set_state(PostStates.waiting_for_city_selection)


@router.message(F.text == "/cancel")
async def cmd_cancel_post(message: Message, state: FSMContext, db):
    """Отмена создания поста на любом этапе"""
    logfire.info(f"Пользователь {message.from_user.id} отменил создание поста")
    await state.clear()
    await message.answer(
        "Создание мероприятия отменено ✖️",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "create_post")
async def start_create_post(callback: CallbackQuery, state: FSMContext, db):
    """Начать создание поста через инлайн-кнопку"""
    await state.set_state(PostStates.creating_post)
    all_cities = await CityService.get_all_cities(db)

    try:
        await callback.message.delete()
    except Exception as e:
        logfire.warning(f"Не удалось удалить сообщение: {e}")

    await callback.message.answer(
        "🎓 Выберите университет(ы) для мероприятия:",
        reply_markup=get_city_keyboard(all_cities, for_post=True),
    )
    await state.set_state(PostStates.waiting_for_city_selection)
    await callback.answer()


@router.callback_query(F.data == "cancel_post")
async def cancel_post_creation(callback: CallbackQuery, state: FSMContext, db):
    """Отмена создания поста — с возвратом через гифку главного меню"""
    await state.clear()

    try:
        await callback.message.delete()
    except Exception as e:
        logfire.warning(f"Не удалось удалить сообщение при отмене: {e}")

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
            logfire.warning(f"Ошибка отправки гифки при отмене: {e}")

    await callback.message.answer(
        "✨ Главное меню",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(PostStates.waiting_for_city_selection, F.data == "post_city_select_all")
async def select_all_cities_post(callback: CallbackQuery, state: FSMContext, db):
    """Переключение: выбрать все / снять все университеты для поста"""
    all_cities = await CityService.get_all_cities(db)
    all_city_ids = [c.id for c in all_cities]

    data = await state.get_data()
    selected_ids = data.get('selected_city_ids', [])

    if len(selected_ids) == len(all_city_ids):
        new_selection = []
        await callback.answer("Все университеты сняты")
    else:
        new_selection = all_city_ids
        await callback.answer("Все университеты выбраны")

    await state.update_data(selected_city_ids=new_selection)

    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(all_cities, new_selection, for_post=True)
    )


@router.callback_query(PostStates.waiting_for_city_selection, F.data == "post_city_confirm")
async def confirm_city_selection(callback: CallbackQuery, state: FSMContext, db):
    """Подтверждение выбора городов для поста"""
    data = await state.get_data()
    selected_ids = data.get('selected_city_ids', [])
    
    if not selected_ids:
        await callback.answer("Выберите хотя бы один университет")
        return
    
    cities = await CityService.get_cities_by_ids(db, selected_ids)
    city_names = [c.name for c in cities]
    await state.update_data(post_city_names=city_names)
    
    all_categories = await CategoryService.get_all_categories(db)
    
    city_text = ", ".join(city_names)
    await callback.message.edit_text(
        f"Университеты выбраны: {city_text}\n\n⭐️ Теперь выберите категории мероприятия:",
        reply_markup=get_category_selection_keyboard(all_categories, for_post=True),
    )
    await state.set_state(PostStates.waiting_for_category_selection)
    await callback.answer()


@router.callback_query(PostStates.waiting_for_city_selection, F.data.startswith("post_city_"))
async def process_post_city_selection(callback: CallbackQuery, state: FSMContext, db):
    """Обработка выбора города для поста"""
    city_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected_ids = data.get('selected_city_ids', [])
    
    if city_id in selected_ids:
        selected_ids.remove(city_id)
    else:
        selected_ids.append(city_id)
    
    await state.update_data(selected_city_ids=selected_ids)
    
    all_cities = await CityService.get_all_cities(db)
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(all_cities, selected_ids, for_post=True)
    )
    await callback.answer()

# --- Остальные обработчики без изменений ---

@router.callback_query(PostStates.waiting_for_category_selection, F.data.startswith("post_category_"))
async def process_post_category_selection(callback: CallbackQuery, state: FSMContext, db):
    """Мультивыбор категорий для поста"""
    category_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    category_ids = data.get("category_ids", [])

    if category_id in category_ids:
        category_ids.remove(category_id)
    else:
        category_ids.append(category_id)
    await state.update_data(category_ids=category_ids)

    all_categories = await CategoryService.get_all_categories(db)
    try:
        await callback.message.edit_text(
            "⭐️ Выберите одну или несколько категорий для мероприятия:",
            reply_markup=get_category_selection_keyboard(all_categories, category_ids, for_post=True),
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()


@router.callback_query(PostStates.waiting_for_category_selection, F.data == "confirm_post_categories")
@logger.catch
async def confirm_post_categories(callback: CallbackQuery, state: FSMContext, db):
    """Подтверждение выбора категорий для поста"""
    data = await state.get_data()
    category_ids = data.get("category_ids", [])
    if not category_ids:
        await callback.answer("Выберите хотя бы одну категорию", show_alert=True)
        return

    stmt = select(Category).where(Category.id.in_(category_ids))
    result = await db.execute(stmt)
    categories = result.scalars().all()

    if categories:
        category_names = [cat.name for cat in categories]
        category_list = ", ".join(category_names)
    else:
        category_list = "Неизвестные категории"

    await state.update_data(category_ids=category_ids)
    logfire.info(f"Категории подтверждены для пользователя {callback.from_user.id}: {category_names}")

    try:
        await callback.message.edit_text(
            f"📝 Создание мероприятия в категориях: {category_list}\n\nВведите заголовок:"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

    await state.set_state(PostStates.waiting_for_title)
    logfire.info(f"Состояние изменено на waiting_for_title для пользователя {callback.from_user.id}")
    await callback.answer()


@router.message(PostStates.waiting_for_title)
@logger.catch
async def process_post_title(message: Message, state: FSMContext, db):
    """Обработка заголовка поста"""
    logfire.info(f"Получен заголовок поста от пользователя {message.from_user.id}: {message.text}")

    if len(message.text) > 100:
        await message.answer("× Заголовок слишком длинный. Максимум 100 символов. Пожалуйста, сократите его и отправьте повторно")
        return

    await state.update_data(title=message.text)
    logfire.info(f"Заголовок сохранен в состоянии: {message.text}")
    await message.answer("Введите описание мероприятия:")
    await state.set_state(PostStates.waiting_for_content)
    logfire.info(f"Состояние изменено на waiting_for_content для пользователя {message.from_user.id}")


@router.message(PostStates.waiting_for_content)
async def process_post_content(message: Message, state: FSMContext, db):
    """Обработка содержания поста"""
    content = message.text
    
    # Проверка длины описания
    if len(content) > MAX_CONTENT_LENGTH:
        await message.answer(f"× Описание слишком длинное. Максимум {MAX_CONTENT_LENGTH} символов. Пожалуйста, сократите его и отправьте повторно")
        return

    await state.update_data(content=content)
    await message.answer(
        "🔗 Введите ссылку на сайт, канал или сообщество мероприятия (или контакты организатора в формате https://).\n\nЭта ссылка будет прикреплена к вашему анонсу:"
    )
    await state.set_state(PostStates.waiting_for_url)


@router.message(PostStates.waiting_for_url)
async def process_post_url(message: Message, state: FSMContext, db):
    """Обработка ссылки для поста с ограничением в 500 символов"""
    url = None if message.text == "/skip" else message.text.strip()

    # Пропуск разрешён
    if url is None:
        await state.update_data(url=url)
        await message.answer(
            "🗓 Введите дату и время события в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2025 18:30)\n\n"
        )
        await state.set_state(PostStates.waiting_for_event_datetime)
        return

    # Проверка длины
    if len(url) > 100:
        await message.answer(
            "× Ссылка слишком длинная — более 100 символов.\n"
            "Пожалуйста, сократите её (например, через bit.ly) или используйте более короткую."
        )
        return

    # Проверка формата URL
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "× Ссылка должна начинаться с http:// или https://. "
            "Попробуйте снова или отправьте /skip."
        )
        return

    # Сохраняем и переходим дальше
    await state.update_data(url=url)
    await message.answer(
        "🗓 Введите дату и время события в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2025 18:30)\n\n"
    )
    await state.set_state(PostStates.waiting_for_event_datetime)


@router.message(PostStates.waiting_for_event_datetime)
async def process_event_datetime(message: Message, state: FSMContext, db):
    """Обработка даты/времени события"""
    from datetime import datetime, timedelta

    try:
        from zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None

    text = message.text.strip()
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y %H.%M"):
        try:
            event_dt = datetime.strptime(text, fmt)

            if ZoneInfo is not None:
                msk = ZoneInfo("Europe/Moscow")
                current_msk = datetime.now(msk).replace(tzinfo=None)
            else:
                current_utc = datetime.now(timezone.utc)
                current_msk = current_utc.replace(tzinfo=None) + timedelta(hours=3)

            min_future_time = current_msk + timedelta(minutes=30)

            if event_dt <= min_future_time:
                await message.answer(
                    "✖️ Время события должно быть не ранее, чем через 30 минут!\n"
                    f"Сейчас: {current_msk.strftime('%d.%m.%Y %H:%M')} (МСК)\n"
                    f"Минимальное время: {min_future_time.strftime('%d.%m.%Y %H:%M')} (МСК)\n"
                    "Выберите время в будущем."
                )
                return

            await state.update_data(event_at=event_dt.isoformat())
            await message.answer("📍 Введите локацию или адрес мероприятия:")
            await state.set_state(PostStates.waiting_for_address)
            return
        except ValueError:
            continue
    await message.answer("✖️ Неверный формат. Пример: 25.12.2025 18:30. Попробуйте снова.")


@router.message(PostStates.waiting_for_address)
async def process_post_address(message: Message, state: FSMContext, db):
    """Обработка адреса мероприятия"""
    address = message.text.strip()
    if len(address) > 200:
        await message.answer("× Адрес слишком длинный. Максимум 200 символов.")
        return

    await state.update_data(address=address)
    await message.answer("🎆 Отправьте изображение для мероприятия (или нажмите /skip для пропуска):")
    await state.set_state(PostStates.waiting_for_image)


@router.message(PostStates.waiting_for_image)
async def process_post_image(message: Message, state: FSMContext, db):
    """Обработка изображения поста"""
    if message.text == "/skip":
        await continue_post_creation(message, state, db)
        return

    if not message.photo:
        await message.answer("× Пожалуйста, отправьте изображение или нажмите /skip")
        return

    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_data = await message.bot.download_file(file_info.file_path)
    file_id = await file_storage.save_file(file_data.read(), "jpg")

    await state.update_data(image_id=file_id)
    await continue_post_creation(message, state, db)


@router.callback_query(PostStates.waiting_for_image, F.data == "skip_image")
async def skip_image_callback(callback: CallbackQuery, state: FSMContext, db):
    await continue_post_creation(callback, state, db)


async def continue_post_creation(callback_or_message: Union[Message, CallbackQuery], state: FSMContext, db):
    """Продолжение создания поста после загрузки изображения"""
    user_id = callback_or_message.from_user.id
    message = (
        callback_or_message
        if isinstance(callback_or_message, Message)
        else callback_or_message.message
    )
    data = await state.get_data()
    title = data.get("title")
    content = data.get("content")
    category_ids = data.get("category_ids", [])
    post_city_names = data.get("post_city_names", [])
    image_id = data.get("image_id")
    event_at_iso = data.get("event_at")
    url = data.get("url")
    address = data.get("address")

    if not all([title, content, category_ids, post_city_names]):
        await message.answer(
            "✖️ Ошибка: не все данные поста заполнены. Попробуйте создать пост заново.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    post = await PostService.create_post_and_send_to_moderation(
        db=db,
        title=title,
        content=content,
        author_id=user_id,
        category_ids=category_ids,
        city_names=post_city_names,
        image_id=image_id,
        event_at=event_at_iso,
        url=url,
        address=address,
        bot=message.bot,
    )

    if post:
        await message.answer(
            f"Мероприятие отправлено в Сердце и будет автоматически опубликовано после модерации 👏🥳",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
    else:
        await message.answer(
            "✖️ Ошибка при создании поста. Попробуйте еще раз.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
