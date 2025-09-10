from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, insert
from sqlalchemy.orm import selectinload
from typing import List, Optional
from ..models import User, Category, City, user_categories, user_cities
from ..models import Post, Like, ModerationRecord, post_categories


class UserRepository:
    """Асинхронный репозиторий для работы с пользователями"""

    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        user = User(
            id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        user = await UserRepository.get_by_telegram_id(db, telegram_id)
        if not user:
            user = await UserRepository.create_user(
                db, telegram_id, username, first_name, last_name
            )
        return user

    @staticmethod
    async def add_categories_to_user(
        db: AsyncSession, user_id: int, category_ids: List[int]
    ) -> User:
        await db.execute(
            delete(user_categories).where(user_categories.c.user_id == user_id)
        )
        if category_ids:
            values = [
                {"user_id": user_id, "category_id": category_id}
                for category_id in category_ids
            ]
            await db.execute(insert(user_categories).values(values))
        await db.commit()
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_cities_to_user(
        db: AsyncSession, user_id: int, city_ids: List[int]
    ) -> User:
        await db.execute(
            delete(user_cities).where(user_cities.c.user_id == user_id)
        )
        if city_ids:
            values = [
                {"user_id": user_id, "city_id": city_id} for city_id in city_ids
            ]
            await db.execute(insert(user_cities).values(values))
        await db.commit()
        result = await db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.cities))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_users_by_cities_and_categories(
        db: AsyncSession, city_ids: List[int], category_ids: List[int]
    ) -> List[User]:
        result = await db.execute(
            select(User)
            .distinct()
            .join(User.cities)
            .join(User.categories)
            .where(
                and_(City.id.in_(city_ids), Category.id.in_(category_ids))
            )
        )
        return result.scalars().all()

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Полное удаление пользователя"""
        # Удаляем лайки
        await db.execute(delete(Like).where(Like.user_id == user_id))
        # Удаляем посты
        post_ids = (await db.execute(select(Post.id).where(Post.author_id == user_id))).scalars().all()
        if post_ids:
            await db.execute(delete(Like).where(Like.post_id.in_(post_ids)))
            await db.execute(delete(ModerationRecord).where(ModerationRecord.post_id.in_(post_ids)))
            await db.execute(delete(post_categories).where(post_categories.c.post_id.in_(post_ids)))
            await db.execute(delete(Post).where(Post.id.in_(post_ids)))
        # Удаляем связи с категориями
        await db.execute(delete(user_categories).where(user_categories.c.user_id == user_id))
        # Удаляем связи с городами
        await db.execute(delete(user_cities).where(user_cities.c.user_id == user_id))
        # Удаляем пользователя
        result = await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return result.rowcount > 0
