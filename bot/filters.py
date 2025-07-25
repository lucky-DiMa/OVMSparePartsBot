from classes import User, States
from aiogram.types import Message

class StateFilter:
    def __init__(self, checking_state: States):
        self.checking_state = checking_state

    def __call__(self, _: None = None, user: User | None = None) -> bool:
        return user.parsed_state.state == self.checking_state


def is_command(message: Message):
    for entity in message.entities:
        if entity.type == 'bot_command':
            return entity.extract_from(message.text)[1:]
    return None
