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
import asyncio
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

LIKED_GIF_ID = os.getenv("LIKED_GIF_ID")
POSTS_PER_PAGE = 5
router = Router()

# ID администратора для рассылки (замените на реальный ID)
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))


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
        await callback.answer("Все университеты сняты")
    else:
        new_selection = all_city_ids
        await callback.answer("Все университеты выбраны")

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
        await callback.answer("Выберите хотя бы один университет", show_alert=True)
        return

    await UserService.select_cities(db, callback.from_user.id, selected_ids)
    
    selected_cities = await CityService.get_cities_by_ids(db, selected_ids)
    city_names = ", ".join([c.name for c in selected_cities])
    
    await state.update_data(selected_cities=[]) # Очищаем состояние

    categories = await CategoryService.get_all_categories(db)
    user_categories = await UserService.get_user_categories(db, callback.from_user.id)
    selected_cat_ids = [cat.id for cat in user_categories]

    text_to_send = (
        f"Университеты выбраны: {city_names}\n\n"
        f"⭐️ Теперь выберите категории интересов для кастомизации уведомлений и подборки:"
    )
    keyboard = get_category_selection_keyboard(categories, selected_cat_ids)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(text=text_to_send, reply_markup=keyboard)

    await state.set_state(UserStates.waiting_for_categories)
    await callback.answer()


@router.callback_query(F.data == "change_city")
async def change_city_callback(callback: CallbackQuery, state: FSMContext, db):
    """Изменение города через инлайн-кнопку"""
    all_cities = await CityService.get_all_cities(db)
    user_cities = await UserService.get_user_cities(db, callback.from_user.id)
    selected_ids = [c.id for c in user_cities]
    
    await state.update_data(selected_cities=selected_ids)

    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        "О мероприятиях в каких университетах вы хотите знать?:",
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
        await callback.answer("Ошибка при изменении избранного", show_alert=True)


@router.message(F.text == "/delete_user")
async def cmd_delete_user(message: Message, db):
    """Удаление пользователя и всех его данных"""
    user_id = message.from_user.id
    logfire.info(f"Пользователь {user_id} запросил удаление аккаунта")

    user = await UserService.register_user(
        db=db,
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    if not user:
        await message.answer("Ваш аккаунт уже удалён или не существует.")
        return

    success = await UserService.delete_user(db, user_id)
    if success:
        await message.answer(
            "✅ Ваш аккаунт и все связанные данные (посты, лайки) успешно удалены.\n\n"
            "Если захотите вернуться — просто начните сначала командой /start",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("❌ Ошибка при удалении аккаунта. Попробуйте позже.")

# НОВАЯ КОМАНДА ДЛЯ АДМИНА
@router.message(F.text.startswith("/broadcast ") & (F.from_user.id == ADMIN_USER_ID))
async def cmd_broadcast(message: Message, db):
    """Отправить сообщение всем пользователям (только для администратора)"""
    # Извлекаем текст сообщения после команды
    original_text = message.text[len("/broadcast "):].strip()
    
    if not original_text:
        await message.answer("❌ Пожалуйста, введите текст сообщения после команды /broadcast")
        return

    # Формируем сообщение с префиксом "Команда «Сердца»:" жирным шрифтом
    # Используем HTML-разметку для выделения жирным
    broadcast_text = f"<b>Команда «Сердца»:</b>\n\n{original_text}"

    # Подтверждение отправки
    confirm_msg = await message.answer(f"⏳ Начинаю рассылку сообщения...\n\n{broadcast_text}", parse_mode="HTML")
    
    # Получаем всех пользователей из базы данных
    users = await UserService.get_all_users(db)
    
    if not users:
        await confirm_msg.edit_text("❌ Нет пользователей для отправки сообщения.")
        return

    total_users = len(users)
    success_count = 0
    fail_count = 0
    
    # Отправляем сообщение каждому пользователю
    for user in users:
        try:
            # Отправляем сообщение с HTML-разметкой
            await message.bot.send_message(chat_id=user.id, text=broadcast_text, parse_mode="HTML")
            success_count += 1
            # Небольшая задержка, чтобы избежать ограничений Telegram
            await asyncio.sleep(0.05) 
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            logfire.warning(f"Пользователь {user.id} заблокировал бота, не могу отправить сообщение")
            fail_count += 1
        except TelegramRetryAfter as e:
            # Достигнут лимит запросов, ждем
            logfire.warning(f"Достигнут лимит запросов Telegram, жду {e.retry_after} секунд")
            await asyncio.sleep(e.retry_after)
            # Повторяем попытку для этого пользователя
            try:
                await message.bot.send_message(chat_id=user.id, text=broadcast_text, parse_mode="HTML")
                success_count += 1
            except Exception as e2:
                logfire.error(f"Ошибка повторной отправки сообщения пользователю {user.id}: {e2}")
                fail_count += 1
        except Exception as e:
            logfire.error(f"Ошибка отправки сообщения пользователю {user.id}: {e}")
            fail_count += 1
            
        # Обновляем статус каждые 10 пользователей
        if (success_count + fail_count) % 10 == 0 or (success_count + fail_count) == total_users:
            try:
                await confirm_msg.edit_text(
                    f"⏳ Рассылка сообщения...\n"
                    f"Прогресс: {success_count + fail_count}/{total_users}\n"
                    f"Успешно: {success_count}\n"
                    f"Ошибок: {fail_count}\n\n"
                    f"{broadcast_text}",
                    parse_mode="HTML"
                )
            except Exception:
                pass # Игнорируем ошибки редактирования сообщения о прогрессе

    # Финальный отчет
    await confirm_msg.edit_text(
        f"✅ Рассылка завершена!\n"
        f"Всего пользователей: {total_users}\n"
        f"Успешно: {success_count}\n"
        f"Ошибок: {fail_count}\n\n"
        f"Отправленное сообщение:\n{broadcast_text}",
        parse_mode="HTML"
    )

# ВОССТАНОВЛЕННЫЙ ОБРАБОТЧИК
@router.message(F.text == "/delete_post")
async def cmd_delete_post(message: Message, db):
    """Удаление поста по ID"""
    try:
        # Проверяем, есть ли ID в сообщении
        if len(message.text.split()) < 2:
            await message.answer("❌ Неверный формат команды. Используйте: /delete_post <id>")
            return
            
        post_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /delete_post <id>")
        return

    # Получаем пост для проверки авторства
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        await message.answer("❌ Пост не найден.")
        return

    # Проверяем, что пользователь является автором поста
    if post.author_id != message.from_user.id:
        await message.answer("❌ Вы можете удалять только свои посты.")
        return

    # Удаляем пост
    success = await PostService.delete_post(db, post_id)
    if success:
        await message.answer(f"✅ Пост с ID {post_id} успешно удален.")
    else:
        await message.answer("❌ Ошибка при удалении поста.")

# ВОССТАНОВЛЕННЫЙ ОБРАБОТЧИК
@router.message(F.text == "/liked_posts")
async def cmd_liked_posts(message: Message, db):
    """Обработчик команды /liked_posts — открытие избранного"""
    logfire.info(f"Пользователь {message.from_user.id} открывает избранное через команду")
    
    try:
        await message.delete()
    except Exception:
        pass

    if LIKED_GIF_ID:
        try:
            sent = await message.answer_animation(
                animation=LIKED_GIF_ID,
                caption="❤️ Загружаю избранное...",
                parse_mode="HTML"
            )
            await show_liked_page_from_animation(sent, 0, db, user_id=message.from_user.id)
            return
        except Exception as e:
            logfire.warning(f"Ошибка отправки гифки избранного: {e}")

    posts = await PostService.get_liked_posts(db, message.from_user.id, POSTS_PER_PAGE, 0)
    if not posts:
        await message.answer(
            "У вас пока нет избранных мероприятий\n"
            "Чтобы добавить:\n"
            "• Выберите событие в подборке\n"
            "• Перейдите в подробнее события\n"
            "• Нажмите «В избранное» под постом",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return

    total_posts = await PostService.get_liked_posts_count(db, message.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    text = format_liked_list(posts, 1, total_posts)

    await message.answer(
        text,
        reply_markup=get_liked_list_keyboard(posts, 0, total_pages, start_index=1),
        parse_mode="HTML"
    )

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

# ВОССТАНОВЛЕННЫЙ ОБРАБОТЧИК
@router.message(F.text == "/help")
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """Справка по Сердцу. Основные функции:

💌 Главное меню - /menu

📮 Смотреть подборку - список актуальных мероприятий по заданным интересам и городу

❤️ Мое избранное - список избранных мероприятий

📝 Создать мероприятие - публикация собственного мероприятия в Сердце

⭐️ Изменить категории - смена категорий для получения уведомлений и подборки

🎓 Изменить университет - смена университета для получения уведомлений и подборки

Как использовать:

1. Выберите университет(ы)
2. Выберите категории для получения уведомлений и подборки
3. Создавайте и продвигайте собственные мероприятия
4. Получайте уведомления о новых мероприятиях по вашим вузам и интересам

Создание поста:

• Заголовок: до 100 символов
• Содержание: до 2000 символов
• Мероприятия проходят модерацию перед публикацией

По любым вопросам обращайтесь в поддержку @serdce_help
"""

    await message.answer(help_text, reply_markup=get_main_keyboard())


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

# ВОССТАНОВЛЕННЫЙ ОБРАБОТЧИК
@router.callback_query(F.data == "help")
async def show_help_callback(callback: CallbackQuery):
    """Показать справку через инлайн-кнопку"""
    help_text = """Справка по Сердцу. Основные функции:

💌 Главное меню - /menu

📮 Смотреть подборку - список актуальных мероприятий по заданным интересам и городу

❤️ Мое избранное - список избранных мероприятий

📝 Создать мероприятие - публикация собственного мероприятия в Сердце

⭐️ Изменить категории - смена категорий для получения уведомлений и подборки

🎓 Изменить университет - смена университета для получения уведомлений и подборки

Как использовать:

1. Выберите университет(ы)
2. Выберите категории для получения уведомлений и подборки
3. Создавайте и продвигайте собственные мероприятия
4. Получайте уведомления о новых мероприятиях по вашим вузам и интересам

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
