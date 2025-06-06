from typing import NamedTuple


class Command(NamedTuple):
    explanation: str


commands = {'/search': Command('Поиск запчастей'),
            '/contacts': Command('Наши контакты'),
            '/feedback': Command('Оставить обратную связь'),
            '/help': Command('Вызвать это сообщение')}