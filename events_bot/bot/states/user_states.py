from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_city = State()           # Устарело, оставлено для совместимости
    waiting_for_cities = State()         # ✅ Новое состояние — выбор нескольких университетов
    waiting_for_categories = State()


class NavigationState(StatesGroup):
    current_section = State()  # 'feed', 'liked', 'menu'
