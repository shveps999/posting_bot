from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService, PostService, LikeService, CityService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_main_keyboard, get_category_selection_keyboard, get_city_keyboard
from events_bot.utils import get_clean_category_string
from events_bot.bot.keyboards.notification_keyboard import get_post_notification_keyboard
from events_bot.bot.handlers.feed_handlers import show_liked_page_from_animation, format_liked_list
from events_bot.bot.keyboards.feed_keyboard import get_liked_list_keyboard
import logfire
import os

LIKED_GIF_ID = os.getenv("LIKED_GIF_ID")
POSTS_PER_PAGE = 5
router = Router()


def register_user_handlers(dp: Router):
    """Регистрация обработчиков пользователя"""
    dp.include_router(router)

# --- Обработка выбора/смены города ---

@router.callback_query(UserStates.waiting_for_city, F.data.startswith("city_"))
async def process_city_selection(callback: CallbackQuery, state: FSMContext, db):
    """Обработка выбора города (множественный выбор)"""
    city_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_ids = data.get("selected_cities", [])

    if city_id in selected_ids:
        selected_ids.remove(city_id)
    else:
        selected_ids.append(city_id)
    await state.update_data(selected_cities=selected_ids)

    all_cities = await CityService.get_all_cities(db)
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(all_cities, selected_ids)
    )
    await callback.answer()


@router.callback_query(UserStates.waiting_for_city, F.data == "user_city_select_all")
async def process_select_all_cities(callback: CallbackQuery, state: FSMContext, db):
    """Обработка кнопки 'Выбрать все' для городов"""
    all_cities = await CityService.get_all_cities(db)
    all_city_ids = [c.id for c in all_cities]

    data = await state.get_data()
    selected_ids = data.get("selected_cities", [])

    if len(selected_ids) == len(all_city_ids):
        new_selection = []
        await callback.answer("🗙 Все университеты сняты")
    else:
        new_selection = all_city_ids
        await callback.answer("✅ Все университеты выбраны!")

    await state.update_data(selected_cities=new_selection)
    await callback.message.edit_reply_markup(
        reply_markup=get_city_keyboard(all_cities, new_selection)
    )


@router.callback_query(UserStates.waiting_for_city, F.data == "confirm_cities")
async def confirm_city_selection(callback: CallbackQuery, state: FSMContext, db):
    """Подтверждение выбора городов"""
    data = await state.get_data()
    selected_ids = data.get("selected_cities", [])
    if not selected_ids:
        await callback.answer("Выберите хотя бы один университет!", show_alert=True)
        return

    await UserService.select_cities(db, callback.from_user.id, selected_ids)
    
    selected_cities = await CityService.get_cities_by_ids(db, selected_ids)
    city_names = ", ".join([c.name for c in selected_cities])
    
    await state.update_data(selected_cities=[]) # Очищаем состояние

    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(db, callback.from_user.id)
    selected_cat_ids = [cat.id for cat in user_categories]

    await callback.message.edit_text(
        f"📍 Университеты выбраны: {city_names}\n\n"
        f"Теперь выберите категории интересов для кастомизации уведомлений и подборки:",
        reply_markup=get_category_selection_keyboard(categories, selected_cat_ids),
    )
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "change_city")
async def change_city_callback(callback: CallbackQuery, state: FSMContext, db):
    """Изменение города через инлайн-кнопку"""
    all_cities = await CityService.get_all_cities(db)
    user_cities = await UserService.get_user_cities(db, callback.from_user.id)
    selected_ids = [c.id for c in user_cities]
    
    await state.update_data(selected_cities=selected_ids) # Сохраняем текущий выбор в состояние

    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        "Выберите университеты для получения уведомлений и подборки:",
        reply_markup=get_city_keyboard(all_cities, selected_ids)
    )
    await state.set_state(UserStates.waiting_for_city)
    await callback.answer()

# --- Остальные обработчики ---

@router.callback_query(F.data.startswith("notify_heart_"))
async def handle_notify_heart(callback: CallbackQuery, db):
    """Обработка нажатия на 'В избранное' в уведомлении"""
    try:
        post_id = int(callback.data.split("notify_heart_")[1])
        user_id = callback.from_user.id

        result = await LikeService.toggle_like(db, user_id, post_id)
        is_liked = result["action"] == "added"
        post = await PostService.get_post_by_id(db, post_id)
        post_url = getattr(post, "url", None)

        new_keyboard = get_post_notification_keyboard(
            post_id=post_id, is_liked=is_liked, url=post_url
        )
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        action_text = "добавлено" if is_liked else "удалено"
        await callback.answer(f"Избранное {action_text}", show_alert=True)
    except Exception:
        await callback.answer("❌ Ошибка при изменении избранного", show_alert=True)


@router.message(F.text == "/my_posts")
async def cmd_my_posts(message: Message, db):
    """Обработчик команды /my_posts"""
    posts = await PostService.get_user_posts(db, message.from_user.id)

    if not posts:
        await message.answer("📭 У вас пока нет постов.", reply_markup=get_main_keyboard())
        return

    response = "📊 Ваши посты:\n\n"
    for post in posts:
        await db.refresh(post, attribute_names=["categories", "cities"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_str = get_clean_category_string(post.categories)
        city_names = ", ".join([c.name for c in post.cities])
        response += f"📝 {post.title}\n"
        response += f"🏙️ {city_names}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"

    await message.answer(response, reply_markup=get_main_keyboard())


@router.message(F.text == "/change_university")
async def cmd_change_city(message: Message, state: FSMContext, db):
    all_cities = await CityService.get_all_cities(db)
    user_cities = await UserService.get_user_cities(db, message.from_user.id)
    selected_ids = [c.id for c in user_cities]
    
    await state.update_data(selected_cities=selected_ids)
    
    await message.answer(
        "Выберите университеты для получения уведомлений и подборки:",
        reply_markup=get_city_keyboard(all_cities, selected_ids)
    )
    await state.set_state(UserStates.waiting_for_city)


@router.message(F.text == "/change_category")
async def cmd_change_category(message: Message, state: FSMContext, db):
    """Обработчик команды /change_category"""
    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(db, message.from_user.id)
    selected_ids = [cat.id for cat in user_categories]

    await message.answer(
        "Выберите категории интересов для получения уведомлений и подборки:",
        reply_markup=get_category_selection_keyboard(categories, selected_ids),
    )
    await state.set_state(UserStates.waiting_for_categories)


@router.callback_query(F.data == "change_category")
async def change_category_callback(callback: CallbackQuery, state: FSMContext, db):
    """Изменение категории через инлайн-кнопку"""
    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(db, callback.from_user.id)
    selected_ids = [cat.id for cat in user_categories]

    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "Выберите категории интересов для кастомизации уведомлений и подборки:",
        reply_markup=get_category_selection_keyboard(categories, selected_ids),
    )
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "my_posts")
async def show_my_posts_callback(callback: CallbackQuery, db):
    """Показать посты пользователя через инлайн-кнопку"""
    posts = await PostService.get_user_posts(db, callback.from_user.id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if not posts:
        await callback.message.answer("📭 У вас пока нет постов.", reply_markup=get_main_keyboard())
        return

    response = "📊 Ваши посты:\n\n"
    for post in posts:
        await db.refresh(post, attribute_names=["categories", "cities"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_str = get_clean_category_string(post.categories)
        city_names = ", ".join([c.name for c in post.cities])
        response += f"📝 {post.title}\n"
        response += f"🏙️ {city_names}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"
    
    await callback.message.answer(response, reply_markup=get_main_keyboard())
    await callback.answer()
