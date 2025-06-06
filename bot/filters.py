from classes import User
from aiogram.types import Message

class StateFilter:
    def __init__(self, checking_state: str, startswith: bool = False):
        self.checking_state = checking_state
        self.startswith = startswith

    def __call__(self, _: None = None, user: User | None = None) -> bool:
        return user.state.startswith(self.checking_state) if self.startswith else (self.checking_state == user.state)


def is_command(message: Message):
    for entity in message.entities:
        if entity.type == 'bot_command':
            return entity.get_text(message.text)[1:]
    return None
