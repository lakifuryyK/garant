from aiogram.fsm.state import State, StatesGroup


class WalletStates(StatesGroup):
    waiting_for_ton = State()
    waiting_for_rub = State()


class DealStates(StatesGroup):
    choosing_currency = State()
    entering_amount = State()
    entering_description = State()


class LanguageStates(StatesGroup):
    choosing_language = State()
