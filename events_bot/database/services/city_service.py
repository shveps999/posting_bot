from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..repositories import CityRepository
from ..models import City


class CityService:
    """Асинхронный сервис для работы с городами"""

    @staticmethod
    async def get_all_cities(db: AsyncSession) -> List[City]:
        """Получить все доступные города"""
        return await CityRepository.get_all_active(db)

    @staticmethod
    async def get_city_by_id(
        db: AsyncSession, city_id: int
    ) -> Optional[City]:
        """Получить город по ID"""
        return await CityRepository.get_by_id(db, city_id)

    @staticmethod
    async def get_cities_by_ids(
        db: AsyncSession, city_ids: List[int]
    ) -> List[City]:
        """Получить города по списку ID"""
        return await CityRepository.get_by_ids(db, city_ids)
