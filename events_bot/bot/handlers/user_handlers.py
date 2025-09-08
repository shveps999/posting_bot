from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from events_bot.database.services import UserService, CategoryService, PostService, LikeService
from events_bot.bot.states import UserStates
from events_bot.bot.keyboards import get_main_keyboard, get_category_selection_keyboard, get_city_keyboard
from events_bot.utils import get_clean_category_string

router = Router()


@router.callback_query(F.data.startswith("notify_heart_"))
async def handle_notify_heart(callback: CallbackQuery, db):
    """Обработка нажатия на 'В избранное' в уведомлении"""
    try:
        post_id = int(callback.data.split("notify_heart_")[1])
        user_id = callback.from_user.id

        # Переключаем лайк
        result = await LikeService.toggle_like(db, user_id, post_id)
        is_liked = result["action"] == "added"

        # Получаем URL поста
        post = await PostService.get_post_by_id(db, post_id)
        post_url = getattr(post, "url", None)

        # Обновляем клавиатуру
        from events_bot.bot.keyboards.notification_keyboard import get_post_notification_keyboard
        new_keyboard = get_post_notification_keyboard(
            post_id=post_id,
            is_liked=is_liked,
            url=post_url
        )
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)

        # Ответ пользователю
        action_text = "добавлено" if is_liked else "удалено"
        await callback.answer(f"Избранное {action_text}", show_alert=True)

    except Exception as e:
        await callback.answer("❌ Ошибка при изменении избранного", show_alert=True)


def register_user_handlers(dp: Router):
    """Регистрация обработчиков пользователя"""
    dp.include_router(router)


@router.message(F.text.in_(["/menu", "/main_menu"]))
async def cmd_main_menu(message: Message):
    """Обработчик команды /menu для главного меню"""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "/my_posts")
async def cmd_my_posts(message: Message, db):
    """Обработчик команды /my_posts"""
    posts = await PostService.get_user_posts(db, message.from_user.id)

    if not posts:
        await message.answer(
            "📭 У вас пока нет постов.", reply_markup=get_main_keyboard()
        )
        return

    response = "📊 Ваши посты:\n\n"
    for post in posts:
        await db.refresh(post, attribute_names=["categories"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_str = get_clean_category_string(post.categories)
        post_city = getattr(post, "city", "Не указан")
        response += f"📝 {post.title}\n"
        response += f"🏙️ {post_city}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"

    await message.answer(response, reply_markup=get_main_keyboard())


@router.message(F.text == "/change_city")
async def cmd_change_city(message: Message, state: FSMContext):
    """Обработчик команды /change_city"""
    await message.answer("Выберите город для получения уведомлений и подборки:", reply_markup=get_city_keyboard())
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


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """Справка по Сердцу. Основные функции:

💌 Главное меню - /menu

📮 Смотреть подборку - список актуальных мероприятий по заданным интересам и городу

❤️ Мое избранное - список избранных мероприятий

✏️ Создать мероприятие - публикация собственного мероприятия в Сердце

⭐️ Изменить категории - смена категорий для получения уведомлений и подборки

📍 Изменить город - смена города для получения уведомлений и подборки

Как использовать:

1. Выберите город проживания
2. Выберите категорию для получения уведомлений и подборки
3. Создавайте и продвигайте собственные мероприятия
4. Получайте уведомления о новых мероприятиях по вашему городу и интересам

Создание поста:

• Заголовок: до 100 символов
• Содержание: до 2000 символов
• Мероприятия проходят модерацию перед публикацией

По любым вопросам обращайтесь в поддержку @serdce_help
"""

    await message.answer(help_text, reply_markup=get_main_keyboard())


@router.callback_query(F.data.startswith("city_"))
async def process_city_selection_callback(
    callback: CallbackQuery, state: FSMContext, db
):
    """Обработка выбора города через инлайн-кнопку"""
    city = callback.data[5:]
    user = await UserService.register_user(
        db=db,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )
    user.city = city
    await db.commit()
    categories = await CategoryService.get_all_categories(db)
    try:
        await callback.message.delete()
        await callback.message.answer(
            f"📍 Город {city} выбран!\n\nТеперь выберите категории интересов для кастомизации уведомлений и подборки:",
            reply_markup=get_category_selection_keyboard(categories),
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "change_city")
async def change_city_callback(callback: CallbackQuery, state: FSMContext):
    """Изменение города через инлайн-кнопку"""
    try:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите город для кастомизации уведомлений и подборки:", reply_markup=get_city_keyboard()
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await state.set_state(UserStates.waiting_for_city)
    await callback.answer()


@router.callback_query(F.data == "change_category")
async def change_category_callback(callback: CallbackQuery, state: FSMContext, db):
    """Изменение категории через инлайн-кнопку"""
    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(db, callback.from_user.id)
    selected_ids = [cat.id for cat in user_categories]

    try:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите категории интересов для кастомизации уведомлений и подборки:",
            reply_markup=get_category_selection_keyboard(categories, selected_ids),
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "my_posts")
async def show_my_posts_callback(callback: CallbackQuery, db):
    """Показать посты пользователя через инлайн-кнопку"""
    posts = await PostService.get_user_posts(db, callback.from_user.id)

    if not posts:
        try:
            await callback.message.delete()
            await callback.message.answer(
                "📭 У вас пока нет постов.", reply_markup=get_main_keyboard()
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                raise
        return

    response = "📊 Ваши посты:\n\n"
    for post in posts:
        await db.refresh(post, attribute_names=["categories"])
        status = "✅ Одобрен" if post.is_approved else "⏳ На модерации"
        category_str = get_clean_category_string(post.categories)
        post_city = getattr(post, "city", "Не указан")
        response += f"📝 {post.title}\n"
        response += f"🏙️ {post_city}\n"
        response += f"📂 {category_str}\n"
        response += f"📅 {post.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += f"📊 {status}\n\n"

    try:
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=get_main_keyboard())
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help_callback(callback: CallbackQuery):
    """Показать справку через инлайн-кнопку"""
    help_text = """Справка по Сердцу. Основные функции:

💌 Главное меню - /menu

📮 Смотреть подборку - список актуальных мероприятий по заданным интересам и городу

❤️ Мое избранное - список избранных мероприятий

✏️ Создать мероприятие - публикация собственного мероприятия в Сердце

⭐️ Изменить категории - смена категорий для получения уведомлений и подборки

📍 Изменить город - смена города для получения уведомлений и подборки

Как использовать:

1. Выберите город проживания
2. Выберите категорию для получения уведомлений и подборки
3. Создавайте и продвигайте собственные мероприятия
4. Получайте уведомления о новых мероприятиях по вашему городу и интересам

Создание поста:

• Заголовок: до 100 символов
• Содержание: до 2000 символов
• Мероприятия проходят модерацию перед публикацией

По любым вопросам обращайтесь в поддержку @serdce_help
"""

    try:
        await callback.message.delete()
        await callback.message.answer(help_text, reply_markup=get_main_keyboard())
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def show_main_menu_callback(callback: CallbackQuery):
    """Обработчик кнопки возврата в главное меню"""
    try:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()
