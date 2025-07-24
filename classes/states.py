from __future__ import annotations

from enum import Enum
from typing import NamedTuple, Callable
from utils import query_type_name


def create_const_context_resolver(context: dict[str, str]) -> Callable[..., dict[str, str]]:
    def resolver(_) -> dict[str, str]:
        return context
    return resolver


def query_type_context_resolver(type_: str) -> dict[str, str]:
    return {"query_type": query_type_name[type_]}



class StateInfo(NamedTuple):
    explanation_template: str
    context_resolver: Callable[[str], dict[str, str]] | dict[str, str] = create_const_context_resolver({})
    is_user_registered: bool = True


class States(Enum):
    JUST_STARTED = StateInfo('Только что впервые зашел в бота', is_user_registered=False)
    SENDING_CONTACT = StateInfo('Отправляет контакт для регистрации', is_user_registered=False)
    WAITING_FOR_REG_CONFIRMATION = StateInfo('Ожидает подтверждения регистрации', is_user_registered=False)
    TYPING_QUERY = StateInfo('Пишет запрос, тип: <code>{query_type}</code>', query_type_context_resolver)
    TYPING_FEEDBACK = StateInfo('Пишет сообщение обратной связи')
    NONE = StateInfo('Бездействует')


class State:
    DELIMITER = '||'

    def __init__(self, state: States, target: str = None):
        self.state = state
        self.target = target

    @classmethod
    def parse(cls, state: str) -> State:
        split_res = state.split(cls.DELIMITER, 1)
        state_name = split_res[0]
        if len(split_res) > 1:
            target = split_res[1]
        else:
            target = None
        return State(States._member_map_[state_name], target)

    @property
    def serialization(self) -> str:
        if not self.target:
            return self.state.name
        return f'{self.state.name}{self.DELIMITER}{str(self.target)}'

    @property
    def explanation(self) -> str:
        return self.state.value.explanation_template.format(**self.state.value.context_resolver(self.target))
