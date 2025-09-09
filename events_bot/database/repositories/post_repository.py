from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, insert, or_, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from ..models import Post, ModerationRecord, ModerationAction, Category, post_categories
from ..models import User, Like
import json

class PostRepository:
    """Асинхронный репозиторий для работы с постами"""
    
    @staticmethod
    async def create_post(
        db: AsyncSession,
        title: str,
        content: str,
        author_id: int,
        category_ids: List[int],
        cities: List[str],
        image_id: str | None = None,
        event_at: datetime | None = None,
        url: str | None = None,
        address: str | None = None,
    ) -> Post:
        """Создать новый пост с категориями, городами и адресом"""
        # Получаем категории
        categories_result = await db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        category_objs = categories_result.scalars().all()
        
        # Преобразуем список городов в JSON строку
        cities_str = json.dumps(cities) if cities else None
        
        post = Post(
            title=title,
            content=content,
            author_id=author_id,
            cities=cities_str,
            image_id=image_id,
            event_at=event_at,
            url=url,
            address=address,
            categories=category_objs,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post
    
    @staticmethod
    async def get_post_cities(db: AsyncSession, post_id: int) -> List[str]:
        """Получить список городов поста"""
        result = await db.execute(select(Post.cities).where(Post.id == post_id))
        cities_str = result.scalar_one_or_none()
        if cities_str:
            try:
                return json.loads(cities_str)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @staticmethod
    async def get_pending_moderation(db: AsyncSession) -> List[Post]:
        result = await db.execute(
            select(Post)
            .where(and_(Post.is_approved == False, Post.is_published == False))
            .options(selectinload(Post.author), selectinload(Post.categories))
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
            .options(selectinload(Post.author), selectinload(Post.categories))
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
            .options(selectinload(Post.author), selectinload(Post.categories))
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
            .options(selectinload(Post.categories))
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int) -> Optional[Post]:
        result = await db.execute(
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.author), selectinload(Post.categories))
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
        # Получаем города пользователя
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
            
        # Получаем города пользователя
        try:
            user_cities = json.loads(user.cities) if user.cities else []
        except (json.JSONDecodeError, TypeError):
            user_cities = []
            
        if not user_cities:
            return []
        
        # Получаем категории пользователя
        user_categories_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user_with_categories = user_categories_result.scalar_one_or_none()
        
        if not user_with_categories or not user_with_categories.categories:
            return []
            
        category_ids = [cat.id for cat in user_with_categories.categories]
        
        # Создаем условия для поиска по городам
        city_conditions = []
        for city in user_cities:
            city_conditions.append(Post.cities.contains(f'"{city}"'))
        
        now_utc = func.now()
        result = await db.execute(
            select(Post)
            .group_by(Post.id)
            .join(Post.categories)
            .where(
                and_(
                    or_(*city_conditions),
                    Post.categories.any(Category.id.in_(category_ids)),
                    Post.is_approved == True,
                    Post.is_published == True,
                    or_(Post.event_at.is_(None), Post.event_at > now_utc),
                )
            )
            .options(selectinload(Post.author), selectinload(Post.categories))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_feed_posts_count(db: AsyncSession, user_id: int) -> int:
        # Получаем города пользователя
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return 0
            
        # Получаем города пользователя
        try:
            user_cities = json.loads(user.cities) if user.cities else []
        except (json.JSONDecodeError, TypeError):
            user_cities = []
            
        if not user_cities:
            return 0
        
        # Получаем категории пользователя
        user_categories_result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user_with_categories = user_categories_result.scalar_one_or_none()
        
        if not user_with_categories or not user_with_categories.categories:
            return 0
            
        category_ids = [cat.id for cat in user_with_categories.categories]
        
        # Создаем условия для поиска по городам
        city_conditions = []
        for city in user_cities:
            city_conditions.append(Post.cities.contains(f'"{city}"'))
        
        result = await db.execute(
            select(func.count(Post.id))
            .join(Post.categories)
            .where(
                and_(
                    or_(*city_conditions),
                    Post.categories.any(Category.id.in_(category_ids)),
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
        # Получаем города пользователя
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
            
        # Получаем города пользователя
        try:
            user_cities = json.loads(user.cities) if user.cities else []
        except (json.JSONDecodeError, TypeError):
            user_cities = []
            
        if not user_cities:
            return []
        
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
            .options(selectinload(Post.author), selectinload(Post.categories))
            .order_by(Post.event_at.is_(None), Post.event_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        from ..models import Like
        # Получаем города пользователя
        user_result = await db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return 0
            
        # Получаем города пользователя
        try:
            user_cities = json.loads(user.cities) if user.cities else []
        except (json.JSONDecodeError, TypeError):
            user_cities = []
            
        if not user_cities:
            return 0
        
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
        from ..models import Like, ModerationRecord
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_posts = await db.execute(
            select(Post.id).where(
                Post.event_at.is_not(None), Post.event_at <= current_utc
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
        result = await db.execute(Post.__table__.delete().where(Post.id.in_(post_ids)))
        await db.commit()
        return result.rowcount or 0
    
    @staticmethod
    async def get_expired_posts_info(db: AsyncSession) -> list[dict]:
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        result = await db.execute(
            select(Post.id, Post.image_id).where(
                and_(Post.event_at.is_not(None), Post.event_at <= current_utc)
            )
        )
        rows = result.all()
        return [{"id": row[0], "image_id": row[1]} for row in rows]
    
    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int) -> bool:
        """Полное удаление поста по ID"""
        from ..models import Like, ModerationRecord
        # Удаляем лайки
        await db.execute(delete(Like).where(Like.post_id == post_id))
        # Удаляем записи модерации
        await db.execute(delete(ModerationRecord).where(ModerationRecord.post_id == post_id))
        # Удаляем связи с категориями
        await db.execute(delete(post_categories).where(post_categories.c.post_id == post_id))
        # Удаляем сам пост
        result = await db.execute(delete(Post).where(Post.id == post_id))
        await db.commit()
        return result.rowcount > 0
