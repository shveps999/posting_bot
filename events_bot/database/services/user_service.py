from typing import List, Optional
import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories import UserRepository
from ..models import User, Category
import json

class UserService:
    """Асинхронный сервис для работы с пользователями"""
    
    @staticmethod
    async def register_user(
        db: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        cities: Optional[List[str]] = None
    ) -> User:
        """Зарегистрировать пользователя"""
        user = await UserRepository.get_user(db, telegram_id)
        if not user:
            logfire.info(f"Регистрация нового пользователя {telegram_id}")
            user = await UserRepository.create_user(
                db, telegram_id, username, first_name, last_name, cities
            )
        return user
    
    @staticmethod
    async def update_user_cities(db: AsyncSession, user_id: int, cities: List[str]) -> User:
        """Обновить список городов пользователя"""
        logfire.info(f"Обновление городов пользователя {user_id}: {cities}")
        return await UserRepository.update_user_cities(db, user_id, cities)
    
    @staticmethod
    async def get_user_cities(db: AsyncSession, user_id: int) -> List[str]:
        """Получить список городов пользователя"""
        return await UserRepository.get_user_cities(db, user_id)
    
    @staticmethod
    async def select_categories(db: AsyncSession, user_id: int, category_ids: List[int]) -> User:
        """Выбрать категории для пользователя"""
        logfire.info(f"Пользователь {user_id} выбрал категории: {category_ids}")
        return await UserRepository.select_categories(db, user_id, category_ids)
    
    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int) -> List[Category]:
        """Получить категории пользователя"""
        return await UserRepository.get_user_categories(db, user_id)
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя и все связанные данные"""
        logfire.info(f"Удаление пользователя {user_id}")
        return await UserRepository.delete_user(db, user_id)
