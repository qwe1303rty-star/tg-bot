from aiogram.fsm.state import State, StatesGroup


class GenerateState(StatesGroup):
    waiting_prompt = State()


class VideoState(StatesGroup):
    waiting_prompt = State()


class ChatState(StatesGroup):
    chatting = State()
