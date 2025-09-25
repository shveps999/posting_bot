from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..repositories import CityRepository
from ..models import City


class CityService:
    """Асинхронный сервис для работы с городами"""

    @staticmethod
    async def get_all_cities(db: AsyncSession) -> List[City]:
        """Получить все доступные города, отсортированные по возрастанию ID"""
        return await CityRepository.get_all_active_ordered_by_id(db)

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
        """Получить города по списку ID (сохраняется порядок из запроса)"""
        return await CityRepository.get_by_ids(db, city_ids)
