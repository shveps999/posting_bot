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
import os

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

router = Router()

FEED_GIF_ID = os.getenv("FEED_GIF_ID")
LIKED_GIF_ID = os.getenv("LIKED_GIF_ID")
POSTS_PER_PAGE = 5

def register_feed_handlers(dp: Router):
    dp.include_router(router)


@router.message(F.text == "/feed")
async def cmd_feed(message: Message, db):
    try:
        await message.delete()
    except Exception:
        pass

    if FEED_GIF_ID:
        try:
            sent = await message.answer_animation(
                animation=FEED_GIF_ID,
                caption="✨ Загружаю подборку...",
                parse_mode="HTML"
            )
            await show_feed_page_from_animation(sent, 0, db, user_id=message.from_user.id)
            return
        except Exception as e:
            print(f"Ошибка отправки гифки ленты: {e}")
    
    await show_feed_page_cmd(message, 0, db)


@router.callback_query(F.data == "feed")
async def show_feed_callback(callback: CallbackQuery, db):
    try:
        await callback.message.delete()
    except Exception:
        pass

    if FEED_GIF_ID:
        try:
            sent = await callback.message.answer_animation(
                animation=FEED_GIF_ID,
                caption="✨ Загружаю подборку...",
                parse_mode="HTML"
            )
            await show_feed_page_from_animation(sent, 0, db, user_id=callback.from_user.id)
            await callback.answer()
            return
        except Exception as e:
            print(f"Ошибка отправки гифки ленты: {e}")
    
    await show_feed_page(callback, 0, db)
    await callback.answer()


@router.callback_query(F.data == "liked_posts")
async def show_liked(callback: CallbackQuery, db):
    try:
        await callback.message.delete()
    except Exception:
        pass

    if LIKED_GIF_ID:
        try:
            sent = await callback.message.answer_animation(
                animation=LIKED_GIF_ID,
                caption="❤️ Загружаю избранное...",
                parse_mode="HTML"
            )
            await show_liked_page_from_animation(sent, 0, db, user_id=callback.from_user.id)
            await callback.answer()
            return
        except Exception as e:
            print(f"Ошибка отправки гифки избранного: {e}")
    
    await show_liked_page(callback, 0, db)
    await callback.answer()


@router.callback_query(F.data.startswith("feed_"))
async def handle_feed_navigation(callback: CallbackQuery, db):
    data = callback.data.split("_")
    action = data[1]
    try:
        if action in ["prev", "next"]:
            current_page = int(data[2])
            total_pages = int(data[3])
            new_page = (
                max(0, current_page - 1) if action == "prev" else current_page + 1
            )
            await show_feed_page_from_animation(callback.message, new_page, db, user_id=callback.from_user.id)
        elif action == "open":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await show_post_details(callback, post_id, current_page, total_pages, db)
        elif action == "back":
            current_page = int(data[2])
            await show_feed_page_from_animation(callback.message, current_page, db, user_id=callback.from_user.id)
        elif action == "heart":
            post_id = int(data[2])
            current_page = int(data[3])
            total_pages = int(data[4])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.exception("Ошибка навигации по ленте {e}", e=e)
    await callback.answer()


async def show_feed_page_from_animation(message: Message, page: int, db, user_id: int):
    try:
        await message.delete()
    except Exception as e:
        logfire.warning(f"Не удалось удалить сообщение: {e}")

    try:
        posts = await PostService.get_feed_posts(db, user_id, POSTS_PER_PAGE, page * POSTS_PER_PAGE)
        if not posts:
            await message.answer_animation(
                animation=FEED_GIF_ID,
                caption="В актуальном пока нет мероприятий по вашим интересам.\n\n"
                        "Что можно сделать:\n"
                        "• Выбрать другие категории или университеты\n"
                        "• Создать своё мероприятие",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        total_posts = await PostService.get_feed_posts_count(db, user_id)
        total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
        for post in posts:
            await db.refresh(post, attribute_names=["categories"])
        preview_text = format_feed_list(posts, page * POSTS_PER_PAGE + 1, total_posts)
        start_index = page * POSTS_PER_PAGE + 1

        await message.answer_animation(
            animation=FEED_GIF_ID,
            caption=preview_text,
            reply_markup=get_feed_list_keyboard(posts, page, total_pages, start_index=start_index),
            parse_mode="HTML"
        )
    except Exception as e:
        logfire.error(f"Ошибка при отправке ленты с гифкой: {e}")


async def show_liked_page_from_animation(message: Message, page: int, db, user_id: int):
    try:
        await message.delete()
    except Exception as e:
        logfire.warning(f"Не удалось удалить сообщение: {e}")

    try:
        posts = await PostService.get_liked_posts(db, user_id, POSTS_PER_PAGE, page * POSTS_PER_PAGE)
        if not posts:
            await message.answer_animation(
                animation=LIKED_GIF_ID,
                caption="У вас пока нет избранных мероприятий\n\n"
                        "Чтобы добавить:\n"
                        "• Выберите событие в актуальном\n"
                        "• Нажмите «В избранное» под постом",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        total_posts = await PostService.get_liked_posts_count(db, user_id)
        total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
        start_index = page * POSTS_PER_PAGE + 1
        text = format_liked_list(posts, start_index, total_posts)

        await message.answer_animation(
            animation=LIKED_GIF_ID,
            caption=text,
            reply_markup=get_liked_list_keyboard(posts, page, total_pages, start_index=start_index),
            parse_mode="HTML"
        )
    except Exception as e:
        logfire.error(f"Ошибка при отправке избранного с гифкой: {e}")


def format_post_for_feed(post, **kwargs) -> str:
    category_str = get_clean_category_string(getattr(post, "categories", None))
    event_at = getattr(post, "event_at", None)
    event_str = event_at.strftime("%d.%m.%Y %H:%M") if event_at else ""
    
    city_names = [c.name for c in getattr(post, "cities", [])]
    post_city = ", ".join(city_names) or "Не указан"
    address = getattr(post, "address", "Не указан")

    lines = [
        f"⭐️ <i>{category_str}</i>",
        "",
        f"<b>{post.title}</b>",
    ]
    if event_str:
        lines.append(f"<i>🗓 {event_str}</i>")
    lines.append(f"<i>📍 {post_city}, {address}</i>")
    lines.append("")
    lines.append(f"{post.content}")

    return "\n".join(lines)


def format_feed_list(posts, current_position_start: int, total_posts: int) -> str:
    lines = ["", ""]
    for idx, post in enumerate(posts, start=current_position_start):
        category_str = get_clean_category_string(post.categories)
        event_at = getattr(post, "event_at", None)
        event_str = event_at.strftime("%d.%m.%Y %H:%M") if event_at else ""
        lines.append(f"{idx}. <b>{post.title}</b>")
        lines.append(f"<i>   ⭐️ {category_str}</i>")
        lines.append(f"<i>   🗓 {event_str}</i>")
        lines.append("")
    lines.append("<b>Подробнее о мероприятии – нажмите на число ниже</b>")
    return "\n".join(lines)


def format_liked_list(posts, current_position_start: int, total_posts: int) -> str:
    lines = ["", ""]
    for idx, post in enumerate(posts, start=current_position_start):
        category_str = get_clean_category_string(post.categories)
        event_at = getattr(post, "event_at", None)
        event_str = event_at.strftime("%d.%m.%Y %H:%M") if event_at else ""
        city_names = [c.name for c in getattr(post, "cities", [])]
        post_city = ", ".join(city_names) or "Не указан"
        
        lines.append(f"{idx}. <b>{post.title}</b>")
        lines.append(f"<i>   ⭐️ {category_str}</i>")
        lines.append(f"<i>   🗓 {event_str}</i>")
        lines.append(f"<i>   📍 {post_city}</i>")
        lines.append("")
    
    lines.append("<b>Подробнее о мероприятии – нажмите на число ниже</b>")
    return "\n".join(lines)


async def handle_post_heart(callback: CallbackQuery, post_id: int, db, data):
    try:
        result = await LikeService.toggle_like(db, callback.from_user.id, post_id)
        action_text = "добавлено" if result["action"] == "added" else "удалено"
        await callback.answer(f"Избранное {action_text}", show_alert=True)

        is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post_id)
        current_page, total_pages = int(data[3]), int(data[4])
        section = data[0]

        post = await PostService.get_post_by_id(db, post_id)
        post_url = getattr(post, "url", None)

        keyboard_map = {
            "liked": get_liked_post_keyboard(current_page, total_pages, post_id, is_liked),
            "feed": get_feed_post_keyboard(current_page, total_pages, post_id, is_liked, post_url)
        }
        await callback.message.edit_reply_markup(reply_markup=keyboard_map.get(section))

    except Exception as e:
        logfire.error(f"Ошибка при сохранении сердечка посту {post_id}: {e}")
        await callback.answer("❌ Ошибка при сохранении сердечка", show_alert=True)


async def show_post_details(callback: CallbackQuery, post_id: int, current_page: int, total_pages: int, db):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        await callback.answer("Пост не найден", show_alert=True)
        return
        
    await db.refresh(post, attribute_names=["author", "categories", "cities"])
    is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post.id)
    text = format_post_for_feed(post)
    post_url = getattr(post, "url", None)
    keyboard = get_feed_post_keyboard(current_page, total_pages, post.id, is_liked, post_url)

    if post.image_id and (media_photo := await file_storage.get_media_photo(post.image_id)):
        await callback.message.edit_media(
            media=InputMediaPhoto(media=media_photo.media, caption=text, parse_mode="HTML"),
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("liked_"))
async def handle_liked_navigation(callback: CallbackQuery, db):
    data = callback.data.split("_")
    action = data[1]
    try:
        if action in ["prev", "next"]:
            current_page, total_pages = int(data[2]), int(data[3])
            new_page = max(0, current_page - 1) if action == "prev" else current_page + 1
            await show_liked_page_from_animation(callback.message, new_page, db, user_id=callback.from_user.id)
        elif action == "open":
            post_id, current_page, total_pages = int(data[2]), int(data[3]), int(data[4])
            await show_liked_post_details(callback, post_id, current_page, total_pages, db)
        elif action == "back":
            current_page = int(data[2])
            await show_liked_page_from_animation(callback.message, current_page, db, user_id=callback.from_user.id)
        elif action == "heart":
            post_id = int(data[2])
            await handle_post_heart(callback, post_id, db, data)
    except Exception as e:
        logfire.exception("Ошибка навигации по избранному {e}", e=e)
    await callback.answer()


async def show_liked_post_details(callback: CallbackQuery, post_id: int, current_page: int, total_pages: int, db):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    await db.refresh(post, attribute_names=["author", "categories", "cities"])
    is_liked = await LikeService.is_post_liked_by_user(db, callback.from_user.id, post.id)
    text = format_post_for_feed(post)
    keyboard = get_liked_post_keyboard(current_page, total_pages, post.id, is_liked)

    if post.image_id and (media_photo := await file_storage.get_media_photo(post.image_id)):
        await callback.message.edit_media(
            media=InputMediaPhoto(media=media_photo.media, caption=text, parse_mode="HTML"),
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
