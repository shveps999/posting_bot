from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from ..repositories import UserRepository
from ..models import User, Category, City


class UserService:
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
    async def select_cities(db: AsyncSession, user_id: int, city_names: List[str]) -> User:
        """Сохранить выбранные города пользователя"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        result = await db.execute(select(City).where(City.name.in_(city_names)))
        cities = result.scalars().all()
        existing_names = {c.name for c in cities}
        for name in city_names:
            if name not in existing_names:
                new_city = City(name=name)
                db.add(new_city)
                cities.append(new_city)
        user.cities = cities
        await db.commit()
        await db.refresh(user)
        return user

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
    async def get_users_for_notification(
        db: AsyncSession, category_ids: List[int], city_names: List[str]
    ) -> List[User]:
        return await UserRepository.get_users_by_categories_and_cities(
            db, category_ids, city_names
        )

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        return await UserRepository.delete_user(db, user_id)
