from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from events_bot.database.services import PostService, LikeService
from events_bot.bot.keyboards.main_keyboard import get_main_keyboard
from events_bot.bot.keyboards.feed_keyboard import (
    get_feed_list_keyboard,
    get_feed_post_keyboard,
    get_liked_list_keyboard,
    get_liked_post_keyboard,
)
from events_bot.storage import file_storage
import logfire
from datetime import timezone
from events_bot.utils import get_clean_category_string

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

router = Router()

POSTS_PER_PAGE = 5


def register_feed_handlers(dp: Router):
    dp.include_router(router)


@router.message(F.text == "/feed")
async def cmd_feed(message: Message, db):
    logfire.info(f"Пользователь {message.from_user.id} открывает ленту через команду")
    await show_feed_page_cmd(message, 0, db)


@router.callback_query(F.data == "feed")
async def show_feed_callback(callback: CallbackQuery, db):
    logfire.info(f"Пользователь {callback.from_user.id} открывает ленту")
    await show_feed_page(callback, 0, db)


@router.callback_query(F.data.startswith("feed_"))
async def handle_feed_navigation(callback: CallbackQuery, db):
    data = callback.data.split("_")
    action = data[1]
    logfire.info(f"Пользователь {callback.from_user.id} навигация по ленте: {action}")
    try:
        if action in ["prev", "next"]:
            current_page = int(data[2])
            total_pages = int(data[3])
            new_page = max(0, current_page - 1) if action == "prev" else current_page + 1
            await show_feed_page(callback, new_page, db)
        elif action == "open":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await show_post_details(callback, post_id, current_page, total_pages, db)
        elif action == "back":
            current_page = int(data[2])
            await show_feed_page(callback, current_page, db)
        elif action == "heart":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.exception("Ошибка навигации по ленте {e}", e=e)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    try:
        if callback.message.text:
            await callback.message.edit_text("Выберите действие:", reply_markup=get_main_keyboard())
        elif callback.message.caption:
            await callback.message.edit_caption(caption="Выберите действие:", reply_markup=get_main_keyboard())
        else:
            await callback.message.edit_text("Выберите действие:", reply_markup=get_main_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()


async def show_feed_page_cmd(message: Message, page: int, db):
    logfire.info(f"Пользователь {message.from_user.id} загружает страницу {page} ленты")
    posts = await PostService.get_feed_posts(db, message.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE)
    if not posts:
        logfire.info(f"Пользователь {message.from_user.id} — в ленте нет постов")
        await message.answer(
            "📮 <b>Смотреть подборку</b>\n\n"
            "В подборке пока нет мероприятий по вашим категориям.\n\n"
            "Что можно сделать:\n"
            "• Выбрать другие категории\n"
            "• Создать своё мероприятие\n"
            "• Дождаться появления в подборке новых мероприятий",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        return
    total_posts = await PostService.get_feed_posts_count(db, message.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for post in posts:
        await db.refresh(post, attribute_names=["categories"])
    preview_text = format_feed_list(posts, page * POSTS_PER_PAGE + 1, total_posts)
    start_index = page * POSTS_PER_PAGE + 1
    await message.answer(
        preview_text,
        reply_markup=get_feed_list_keyboard(posts, page, total_pages, start_index=start_index),
        parse_mode="HTML",
    )


async def show_feed_page(callback: CallbackQuery, page: int, db):
    logfire.info(f"Пользователь {callback.from_user.id} загружает страницу {page} ленты")
    posts = await PostService.get_feed_posts(db, callback.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE)
    if not posts:
        logfire.info(f"Пользователь {callback.from_user.id} — в ленте нет постов")
        try:
            if callback.message.text:
                await callback.message.edit_text(
                    "📮 <b>Смотреть подборку</b>\n\n"
                    "В подборке пока нет мероприятий по вашим категориям.\n\n"
                    "Что можно сделать:\n"
                    "• Выбрать другие категории\n"
                    "• Создать своё мероприятие\n"
                    "• Дождаться появления в подборке новых мероприятий",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
            elif callback.message.caption:
                await callback.message.edit_caption(
                    caption="📮 <b>Смотреть подборку</b>\n\n"
                            "В подборке пока нет мероприятий по вашим категориям.\n\n"
                            "Что можно сделать:\n"
                            "• Выбрать другие категории\n"
                            "• Создать своё мероприятие\n"
                            "• Дождаться появления в подборке новых мероприятий",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
        return
    total_posts = await PostService.get_feed_posts_count(db, callback.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for post in posts:
        await db.refresh(post, attribute_names=["categories"])
    preview_text = format_feed_list(posts, page * POSTS_PER_PAGE + 1, total_posts)
    start_index = page * POSTS_PER_PAGE + 1
    try:
        if callback.message.text:
            await callback.message.edit_text(
                preview_text,
                reply_markup=get_feed_list_keyboard(posts, page, total_pages, start_index=start_index),
                parse_mode="HTML",
            )
        elif callback.message.caption:
            await callback.message.edit_caption(
                caption=preview_text,
                reply_markup=get_feed_list_keyboard(posts, page, total_pages, start_index=start_index),
                parse_mode="HTML",
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


def _msk_str(dt) -> str:
    if not dt:
        return ""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_post_for_feed(post, current_position: int, total_posts: int, likes_count: int = 0) -> str:
    category_str = get_clean_category_string(post.categories if hasattr(post, "categories") else None)
    event_at = getattr(post, "event_at", None)
    event_str = _msk_str(event_at)
    lines = [
        f"⭐️ <i>{category_str}</i>",
        f"<b>{post.title}</b>",
        "",
    ]
    if event_str:
        lines.append(f"<i>• {event_str}</i>")
    lines.append(f"<i>• {getattr(post, 'address', 'Не указан')}</i>")
    lines.append("")
    lines.append(f"{post.content}")
    lines.append("")
    lines.append(f"💖 Сердечек: {likes_count}")
    lines.append(f"{current_position} из {total_posts} постов")
    return "\n".join(lines)


def format_feed_list(posts, current_position_start: int, total_posts: int) -> str:
    lines = ["Подборка актуальных мероприятий", ""]
    for idx, post in enumerate(posts, start=current_position_start):
        category_str = get_clean_category_string(post.categories)
        event_at = getattr(post, "event_at", None)
        event_str = _msk_str(event_at)
        lines.append(f"{idx}. <b>{post.title}</b>")
        lines.append(f"<i>   ⭐️ {category_str}</i>")
        lines.append(f"<i>   🗓 {event_str}</i>")
        lines.append("")
    lines.append("Нажмите на число, чтобы смотреть событие подробнее")
    return "\n".join(lines)


def format_liked_list(posts, current_position_start: int, total_posts: int) -> str:
    lines = ["Избранные мероприятия", ""]
    for idx, post in enumerate(posts, start=current_position_start):
        category_str = get_clean_category_string(post.categories)
        event_at = getattr(post, "event_at", None)
        event_str = _msk_str(event_at)
        lines.append(f"{idx}. <b>{post.title}</b>")
        lines.append(f"<i>   ⭐️ {category_str}</i>")
        lines.append(f"<i>   🗓 {event_str}</i>")
        lines.append("")
    lines.append(f"Всего: {total_posts} в избранном")
    lines.append("Нажмите на число, чтобы смотреть событие подробнее")
    return "\n".join(lines)


async def handle_post_heart(callback: CallbackQuery, post_id: int, db, data):
    logfire.info(f"Пользователь {callback.from_user.id} нажал на сердечко посту {post_id}")
    try:
        result = await LikeService.toggle_like(db, callback.from_user.id, post_id)
        action_text = "добавлено" if result["action"] == "added" else "удалено"
        likes_count = result["likes_count"]
        response_text = f"Сердечко {action_text}!\n\n💖 Всего сердечек: {likes_count}"
        await callback.answer(response_text, show_alert=True)

        is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post_id)
        current_page = int(data[3])
        total_pages = int(data[4])
        section = data[0]
        if section == "liked":
            new_keyboard = get_liked_post_keyboard(current_page, total_pages, post_id, is_liked, likes_count)
        else:
            new_keyboard = get_feed_post_keyboard(current_page, total_pages, post_id, is_liked, likes_count)
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        logfire.info(f"Сердечко посту {post_id} успешно {action_text}")
    except Exception as e:
        logfire.error(f"Ошибка при сохранении сердечка посту {post_id}: {e}")
        await callback.answer("❌ Ошибка при сохранении сердечка", show_alert=True)


async def show_post_details(callback: CallbackQuery, post_id: int, current_page: int, total_pages: int, db):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        await callback.answer("Пост не найден", show_alert=True)
        return
    await db.refresh(post, attribute_names=["author", "categories"])
    is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post.id)
    likes_count = await LikeService.get_post_likes_count(db, post.id)
    total_feed_posts = await PostService.get_feed_posts_count(db, callback.from_user.id)
    text = format_post_for_feed(post, current_page + 1, total_feed_posts, likes_count)
    post_url = getattr(post, "url", None)

    if post.image_id:
        media_photo = await file_storage.get_media_photo(post.image_id)
        if media_photo:
            try:
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=media_photo.media, caption=text, parse_mode="HTML"),
                    reply_markup=get_feed_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count, url=post_url),
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
            return
    try:
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=get_feed_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count, url=post_url), parse_mode="HTML")
        elif callback.message.caption:
            await callback.message.edit_caption(caption=text, reply_markup=get_feed_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count, url=post_url), parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


@router.callback_query(F.data == "liked_posts")
async def show_liked(callback: CallbackQuery, db):
    await show_liked_page(callback, 0, db)


@router.callback_query(F.data.startswith("liked_"))
async def handle_liked_navigation(callback: CallbackQuery, db):
    data = callback.data.split("_")
    action = data[1]
    try:
        if action in ["prev", "next"]:
            current_page = int(data[2])
            total_pages = int(data[3])
            new_page = max(0, current_page - 1) if action == "prev" else current_page + 1
            await show_liked_page(callback, new_page, db)
        elif action == "open":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await show_liked_post_details(callback, post_id, current_page, total_pages, db)
        elif action == "back":
            current_page = int(data[2])
            await show_liked_page(callback, current_page, db)
        elif action == "heart":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.exception("Ошибка навигации по избранному {e}", e=e)
    await callback.answer()


async def show_liked_page(callback: CallbackQuery, page: int, db):
    posts = await PostService.get_liked_posts(db, callback.from_user.id, POSTS_PER_PAGE, page * POSTS_PER_PAGE)
    if not posts:
        try:
            if callback.message.text:
                await callback.message.edit_text(
                    "❤️ <b>Мое избранное</b>\n\n"
                    "У вас пока нет избранных мероприятий\n\n"
                    "Чтобы добавить:\n"
                    "• Выберите событие в подборке\n"
                    "• Нажмите на сердце под постом",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
            elif callback.message.caption:
                await callback.message.edit_caption(
                    caption="❤️ <b>Мое избранное</b>\n\n"
                            "У вас пока нет избранных мероприятий\n\n"
                            "Чтобы добавить:\n"
                            "• Выберите событие в подборке\n"
                            "• Нажмите на сердце под постом",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
        return
    total_posts = await PostService.get_liked_posts_count(db, callback.from_user.id)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    start_index = page * POSTS_PER_PAGE + 1
    text = format_liked_list(posts, start_index, total_posts)
    try:
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=get_liked_list_keyboard(posts, page, total_pages, start_index=start_index), parse_mode="HTML")
        elif callback.message.caption:
            await callback.message.edit_caption(caption=text, reply_markup=get_liked_list_keyboard(posts, page, total_pages, start_index=start_index), parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


async def show_liked_post_details(callback: CallbackQuery, post_id: int, current_page: int, total_pages: int, db):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return
    await db.refresh(post, attribute_names=["author", "categories"])
    is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post.id)
    likes_count = await LikeService.get_post_likes_count(db, post.id)
    total_liked = await PostService.get_liked_posts_count(db, callback.from_user.id)
    text = format_post_for_feed(post, current_page + 1, total_liked, likes_count)
    if post.image_id:
        media_photo = await file_storage.get_media_photo(post.image_id)
        if media_photo:
            try:
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=media_photo.media, caption=text, parse_mode="HTML"),
                    reply_markup=get_liked_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count),
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
            return
    try:
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=get_liked_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count), parse_mode="HTML")
        elif callback.message.caption:
            await callback.message.edit_caption(caption=text, reply_markup=get_liked_post_keyboard(current_page, total_pages, post.id, is_liked, likes_count), parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
