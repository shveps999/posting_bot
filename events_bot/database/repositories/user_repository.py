from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from ..models import User, Category, user_categories
import json

class UserRepository:
    """Асинхронный репозиторий для работы с пользователями"""
    
    @staticmethod
    async def get_user(db: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await db.execute(select(User).where(User.id == telegram_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        cities: Optional[List[str]] = None
    ) -> User:
        """Создать нового пользователя"""
        cities_str = json.dumps(cities) if cities else None
        user = User(
            id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            cities=cities_str
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update_user_cities(db: AsyncSession, user_id: int, cities: List[str]) -> User:
        """Обновить список городов пользователя"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.cities = json.dumps(cities) if cities else None
            await db.commit()
            await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_cities(db: AsyncSession, user_id: int) -> List[str]:
        """Получить список городов пользователя"""
        result = await db.execute(select(User.cities).where(User.id == user_id))
        cities_str = result.scalar_one_or_none()
        if cities_str:
            try:
                return json.loads(cities_str)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @staticmethod
    async def update_user(db: AsyncSession, user: User) -> User:
        """Обновить пользователя"""
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            await db.delete(user)
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def select_categories(db: AsyncSession, user_id: int, category_ids: List[int]) -> User:
        """Выбрать категории для пользователя"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            # Получаем категории по ID
            categories_result = await db.execute(
                select(Category).where(Category.id.in_(category_ids))
            )
            categories = categories_result.scalars().all()
            user.categories = categories
            await db.commit()
            await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int) -> List[Category]:
        """Получить категории пользователя"""
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.categories))
        )
        user = result.scalar_one_or_none()
        return user.categories if user else []
    
    @staticmethod
    async def get_users_by_city_and_categories(
        db: AsyncSession, 
        cities: List[str], 
        category_ids: List[int]
    ) -> List[User]:
        """Получить пользователей по городам и категориям"""
        if not cities or not category_ids:
            return []
            
        # Создаем условия для поиска по городам
        city_conditions = []
        for city in cities:
            city_conditions.append(User.cities.contains(f'"{city}"'))
            
        result = await db.execute(
            select(User)
            .where(
                and_(
                    or_(*city_conditions),
                    User.categories.any(Category.id.in_(category_ids)),
                    User.is_active == True
                )
            )
            .options(selectinload(User.categories))
        )
        return result.scalars().all()
