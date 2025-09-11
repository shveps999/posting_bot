from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, insert, or_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from ..models import Post, ModerationRecord, ModerationAction, Category, City, post_categories
from ..models import User, Like


class PostRepository:
    """Асинхронный репозиторий для работы с постами"""

    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        city_names: List[str],
        image_id: str | None = None,
        event_at: datetime | None = None,
        url: str | None = None,
        address: str | None = None,
    ) -> Post:
        """Создать новый пост с категориями, городами и адресом"""
        categories_result = await db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        category_objs = categories_result.scalars().all()

        cities_result = await db.execute(
            select(City).where(City.name.in_(city_names))
        )
        city_objs = cities_result.scalars().all()

        post = Post(
            title=title,
            content=content,
            author_id=author_id,
            image_id=image_id,
            event_at=event_at,
            url=url,
            address=address,
            categories=category_objs,
            cities=city_objs,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def get_pending_moderation(db: AsyncSession) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(and_(Post.is_approved == False, Post.is_published == False))
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
        )
        return result.scalars().all()

    @staticmethod
    async def get_approved_posts(db: AsyncSession) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(
                and_(
                    Post.is_approved == True,
                    (Post.event_at.is_(None) | (Post.event_at > func.now())),
                )
            )
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_posts_by_categories(
        db: AsyncSession, category_ids: List[int]
    ) -> List[Post]:
        result = await db.execute(
            select(Post)
            .distinct()
            .join(Post.categories)
            .where(
                and_(
                    Post.categories.any(Category.id.in_(category_ids)),
                    Post.is_approved == True,
                    Post.is_published == True,
                    (Post.event_at.is_(None) | (Post.event_at > func.now())),
                )
            )
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def approve_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.is_approved = True
            post.is_published = True
            post.published_at = func.now()
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.APPROVE.value,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def reject_post(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.is_approved = False
            post.is_published = False
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.REJECT.value,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def request_changes(
        db: AsyncSession, post_id: int, moderator_id: int, comment: str = None
    ) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            moderation_record = ModerationRecord(
                post_id=post_id,
                moderator_id=moderator_id,
                action=ModerationAction.REQUEST_CHANGES.value,
                comment=comment,
            )
            db.add(moderation_record)
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def get_user_posts(db: AsyncSession, user_id: int) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(Post.author_id == user_id)
            .options(selectinload(Post.categories), selectinload(Post.cities))
        )
        return result.scalars().all()

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        result = await db.execute(
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def publish_post(db: AsyncSession, post_id: int) -> Post:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.is_published = True
            post.published_at = func.now()
            await db.commit()
            await db.refresh(post)
        return post

    @staticmethod
    async def get_feed_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories), selectinload(User.cities))
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.categories or not user.cities:
            return []

        category_ids = [cat.id for cat in user.categories]
        city_ids = [c.id for c in user.cities]
        now_utc = func.now()
        
        result = await db.execute(
            select(Post)
            .group_by(Post.id) # <-- ИЗМЕНЕНИЕ ЗДЕСЬ
            .join(Post.categories)
            .join(Post.cities)
            .where(
                and_(
                    Post.categories.any(Category.id.in_(category_ids)),
                    Post.cities.any(City.id.in_(city_ids)),
                    Post.is_approved == True,
                    Post.is_published == True,
                    or_(Post.event_at.is_(None), Post.event_at > now_utc),
                )
            )
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories), selectinload(User.cities))
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.categories or not user.cities:
            return 0

        category_ids = [cat.id for cat in user.categories]
        city_ids = [c.id for c in user.cities]

        result = await db.execute(
            select(func.count(Post.id.distinct()))
            .join(Post.categories)
            .join(Post.cities)
            .where(
                and_(
                    Post.categories.any(Category.id.in_(category_ids)),
                    Post.cities.any(City.id.in_(city_ids)),
                    Post.is_approved == True,
                    Post.is_published == True,
                    or_(Post.event_at.is_(None), Post.event_at > func.now()),
                )
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def get_liked_posts(
        db: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Post]:
        from ..models import Like
        result = await db.execute(
            select(Post)
            .join(Like, Like.post_id == Post.id)
            .where(
                and_(
                    Like.user_id == user_id,
                    Post.is_approved == True,
                    Post.is_published == True,
                    or_(Post.event_at.is_(None), Post.event_at > func.now()),
                )
            )
            .options(selectinload(Post.author), selectinload(Post.categories), selectinload(Post.cities))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        from ..models import Like
        result = await db.execute(
            select(func.count(Post.id))
            .join(Like, Like.post_id == Post.id)
            .where(
                and_(
                    Like.user_id == user_id,
                    Post.is_approved == True,
                    Post.is_published == True,
                    or_(Post.event_at.is_(None), Post.event_at > func.now()),
                )
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def delete_expired_posts(db: AsyncSession) -> int:
        from ..models import Like, ModerationRecord, post_cities
        # Получаем текущее время UTC
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        # Вычисляем пороговое время: события, которые должны были начаться более 2 часов назад
        # То есть, если event_at + 2 часа <= current_utc, то пост считается просроченным
        expiration_threshold = current_utc - timedelta(hours=2)
        
        expired_posts = await db.execute(
            select(Post.id).where(
                and_(
                    Post.event_at.is_not(None), 
                    Post.event_at <= expiration_threshold
                )
            )
        )
        post_ids = [pid for pid in expired_posts.scalars().all()]
        if not post_ids:
            return 0
        await db.execute(Like.__table__.delete().where(Like.post_id.in_(post_ids)))
        await db.execute(
            ModerationRecord.__table__.delete().where(
                ModerationRecord.post_id.in_(post_ids)
            )
        )
        await db.execute(
            post_categories.delete().where(post_categories.c.post_id.in_(post_ids))
        )
        await db.execute(
            post_cities.delete().where(post_cities.c.post_id.in_(post_ids))
        )
        result = await db.execute(Post.__table__.delete().where(Post.id.in_(post_ids)))
        await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def get_expired_posts_info(db: AsyncSession) -> list[dict]:
        # Получаем текущее время UTC
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        # Вычисляем пороговое время: события, которые должны были начаться более 2 часов назад
        # То есть, если event_at + 2 часа <= current_utc, то пост считается просроченным
        expiration_threshold = current_utc - timedelta(hours=2)
        
        result = await db.execute(
            select(Post.id, Post.image_id).where(
                and_(
                    Post.event_at.is_not(None), 
                    Post.event_at <= expiration_threshold
                )
            )
        )
        rows = result.all()
        return [{"id": row[0], "image_id": row[1]} for row in rows]

    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int) -> bool:
        """Полное удаление поста по ID"""
        from ..models import Like, ModerationRecord, post_cities
        # Удаляем лайки
        await db.execute(delete(Like).where(Like.post_id == post_id))
        # Удаляем записи модерации
        await db.execute(delete(ModerationRecord).where(ModerationRecord.post_id == post_id))
        # Удаляем связи с категориями
        await db.execute(delete(post_categories).where(post_categories.c.post_id == post_id))
        # Удаляем связи с городами
        await db.execute(delete(post_cities).where(post_cities.c.post_id == post_id))
        # Удаляем сам пост
        result = await db.execute(delete(Post).where(Post.id == post_id))
        await db.commit()
        return result.rowcount > 0
