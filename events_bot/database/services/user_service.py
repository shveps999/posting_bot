from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from events_bot.database.models import User, City, UserCity
from typing import List


class UserService:
    @staticmethod
    async def register_user(db: AsyncSession, telegram_id: int, username: str, first_name: str, last_name: str):
        result = await db.execute(select(User).where(User.id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
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
    async def get_user_cities(db: AsyncSession, user_id: int) -> List[City]:
        """Получить все университеты пользователя"""
        result = await db.execute(
            select(City)
            .join(UserCity)
            .where(UserCity.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def select_cities(db: AsyncSession, user_id: int, city_names: list):
        """Сохранить выбранные университеты пользователя"""
        # Удаляем старые связи
        await db.execute(
            UserCity.__table__.delete().where(UserCity.user_id == user_id)
        )
        # Добавляем новые
        cities = await db.execute(
            select(City).where(City.name.in_(city_names))
        )
        city_objects = cities.scalars().all()
        for city in city_objects:
            user_city = UserCity(user_id=user_id, city_id=city.id)
            db.add(user_city)

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
            return True
        return False
