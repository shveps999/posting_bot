from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    waiting_for_city = State()
    waiting_for_cities = State()  # Добавлено новое состояние
    waiting_for_categories = State()


class NavigationState(StatesGroup):
    """Состояние для отслеживания текущего раздела"""
    current_section = State()  # 'feed', 'liked', 'menu'
