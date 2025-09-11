from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from ..repositories import UserRepository
from ..models import User, Category, City


class UserService:
    """Асинхронный сервис для работы с пользователями"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> User:
        return await UserRepository.get_or_create_user(
            db, telegram_id, username, first_name, last_name
        )

    @staticmethod
    async def select_categories(
        db: AsyncSession, user_id: int, category_ids: List[int]
    ) -> User:
        return await UserRepository.add_categories_to_user(db, user_id, category_ids)

    @staticmethod
    async def select_cities(
        db: AsyncSession, user_id: int, city_ids: List[int]
    ) -> User:
        return await UserRepository.add_cities_to_user(db, user_id, city_ids)

    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int) -> List[Category]:
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user = result.scalar_one_or_none()
        return user.categories if user else []

    @staticmethod
    async def get_user_cities(db: AsyncSession, user_id: int) -> List[City]:
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.cities))
        )
        user = result.scalar_one_or_none()
        return user.cities if user else []

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя по ID"""
        return await UserRepository.delete_user(db, user_id)

    # НОВЫЙ МЕТОД ДЛЯ РАССЫЛКИ
    @staticmethod
    async def get_all_users(db: AsyncSession) -> List[User]:
        """Получить всех пользователей"""
        return await UserRepository.get_all_users(db)
