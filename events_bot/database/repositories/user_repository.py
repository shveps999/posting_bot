from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import selectinload
from typing import List, Optional
from ..models import User, City, Category, user_cities, user_categories


class UserRepository:
    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await db.execute(
            select(User).where(User.id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, telegram_id: int, username: str, first_name: str, last_name: str) -> User:
        """Создать нового пользователя"""
        user = User(
            id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user: User, **kwargs) -> None:
        """Обновить данные пользователя"""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await db.flush()

    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int) -> List[Category]:
        """Получить категории пользователя"""
        result = await db.execute(
            select(Category)
            .join(user_categories)
            .where(user_categories.c.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def select_categories(db: AsyncSession, user_id: int, category_ids: list):
        """Сохранить выбранные категории пользователя"""
        await db.execute(
            delete(user_categories).where(user_categories.c.user_id == user_id)
        )
        if category_ids:
            values = [{"user_id": user_id, "category_id": cat_id} for cat_id in category_ids]
            await db.execute(
                insert(user_categories).values(values)
            )

    @staticmethod
    async def get_user_cities(db: AsyncSession, user_id: int) -> List[City]:
        """Получить все университеты пользователя"""
        result = await db.execute(
            select(City)
            .join(user_cities)
            .where(user_cities.c.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def select_cities(db: AsyncSession, user_id: int, city_names: list[str]):
        """Сохранить выбранные университеты пользователя"""
        await db.execute(
            user_cities.delete().where(user_cities.c.user_id == user_id)
        )
        cities = await db.execute(
            select(City).where(City.name.in_(city_names))
        )
        city_objects = cities.scalars().all()
        for city in city_objects:
            await db.execute(
                user_cities.insert().values(user_id=user_id, city_id=city.id)
            )

    @staticmethod
    async def get_all_users(db: AsyncSession) -> List[User]:
        """Получить всех пользователей"""
        result = await db.execute(select(User))
        return list(result.scalars().all())

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя"""
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
            return True
        return False

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await db.get(User, user_id)

    @staticmethod
    async def get_users_by_city(db: AsyncSession, city_name: str) -> List[User]:
        """Получить пользователей по городу"""
        result = await db.execute(
            select(User)
            .join(user_cities)
            .join(City)
            .where(City.name == city_name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_users_by_categories(db: AsyncSession, category_ids: List[int]) -> List[User]:
        """Получить пользователей по категориям"""
        result = await db.execute(
            select(User)
            .join(user_categories)
            .where(user_categories.c.category_id.in_(category_ids))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_users(db: AsyncSession) -> List[User]:
        """Получить активных пользователей"""
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество постов пользователя"""
        result = await db.execute(
            select(func.count(Post.id)).where(Post.author_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_user_liked_posts_count(db: AsyncSession, user_id: int) -> int:
        """Получить количество лайков пользователя"""
        result = await db.execute(
            select(func.count(Like.id)).where(Like.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_user_with_relations(db: AsyncSession, user_id: int) -> Optional[User]:
        """Получить пользователя с категориями и городами"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.categories))
            .options(selectinload(User.cities))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
