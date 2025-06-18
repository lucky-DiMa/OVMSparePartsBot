from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from classes import JsonSerializableObject, RedisObject, SparePart
from utils import RequestsTo1cService, morph


class Analog(JsonSerializableObject):
    fields = {'name': str, 'code': str, 'count': int}
    def __init__(self, name: str, code: str, count: int):
        self.name = name
        self.code = code
        self.count = count

    async def get_full_info(self) -> SparePart:
        return await SparePart.get_by_code(self.code)

class AnalogSearchResult(RedisObject):
    fields = {'name': str, 'code': str, 'analogs': list[Analog]}
    redis_key = 'code'
    redis_TTL = 300
    redis_collection_name = 'analog_search_results'
    def __init__(self, name: str, code: str, analogs: list[Analog]):
        self.analogs = analogs
        self.code = code
        self.name = name

    @classmethod
    async def get_by_code(cls, code: str) -> AnalogSearchResult | None:
        redis_res = await cls.get_from_redis(code)
        if redis_res:
            return redis_res
        json_res = await RequestsTo1cService.get_analogs_by_code(code)
        if not json_res.get('thisisitem', False):
            return None
        json_res = json_res.get('item')
        res = cls(json_res['name'], json_res['code'], list(map(lambda json_analog: Analog(json_analog['nameanalog'], json_analog['analog'], int('0' + json_analog['count'])), json_res['analogs'])))
        await res.save_to_redis()
        return res

    @property
    def text(self) -> str:
        return f'Запрос аналогов для запчасти:\nАртикул: <code>{self.code}</code>\nНазвание: <code>{self.name}</code>\n\nНайдено <code>{len(self.analogs)}</code> {morph.parse("запчасть")[0].make_agree_with_number(len(self.analogs)).word}:'

    def keyboard(self, page_n: int = 0) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for i, analog in enumerate(self.analogs[page_n * 10:min(len(self.analogs), (page_n + 1) * 10)]):
            markup.inline_keyboard.append([InlineKeyboardButton(text=analog.name[:min(20, len(analog.name))] + ('...' if len(analog.name) > 20 else '') + f' ({analog.count} шт.)', callback_data=f'SHOW ASP {page_n * 10 + i}')])
        if self.pages_count > 1:
            markup.inline_keyboard.append([InlineKeyboardButton(text='<<', callback_data=f'GOTO ASP PAGE {page_n - 1}'),
                                           InlineKeyboardButton(text=f'{page_n + 1} / {self.pages_count}', callback_data=f'PAGE NUMBER {page_n + 1} {self.pages_count}'),
                                           InlineKeyboardButton(text='>>', callback_data=f'GOTO ASP PAGE {page_n + 1}')])
        return markup

    @property
    def pages_count(self) -> int:
        return int(len(self.analogs) // 10 + (1 if len(self.analogs) % 10 > 0 else 0))