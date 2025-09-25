from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from ..models import City


class CityRepository:
    """Асинхронный репозиторий для работы с городами"""

    @staticmethod
    async def get_all_active(db: AsyncSession) -> List[City]:
        """Получить все активные города, отсортированные по возрастанию ID"""
        result = await db.execute(
            select(City)
            .where(City.is_active == True)
            .order_by(City.id.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, city_id: int) -> Optional[City]:
        """Получить город по ID"""
        result = await db.execute(select(City).where(City.id == city_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ids(db: AsyncSession, city_ids: List[int]) -> List[City]:
        """Получить города по списку ID (сохраняет порядок из запроса)"""
        result = await db.execute(
            select(City)
            .where(City.id.in_(city_ids))
            .order_by(City.id.asc())  # Опционально: сортировка по ID
        )
        return result.scalars().all()

    @staticmethod
    async def create_city(db: AsyncSession, name: str) -> City:
        """Создать новый город"""
        city = City(name=name)
        db.add(city)
        await db.commit()
        await db.refresh(city)
        return city
