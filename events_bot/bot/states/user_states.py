from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    waiting_for_city = State()           # Устарело, можно оставить для совместимости
    waiting_for_cities = State()         # ✅ Новое состояние — выбор нескольких университетов
    waiting_for_categories = State()


class NavigationState(StatesGroup):
    """Состояние для отслеживания текущего раздела"""
    current_section = State()  # 'feed', 'liked', 'menu'
