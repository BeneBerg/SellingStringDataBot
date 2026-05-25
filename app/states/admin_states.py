from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_for_keys = State()
    waiting_for_price = State()
    waiting_for_welcome = State()
    waiting_for_offer = State()
    waiting_for_instruction = State()