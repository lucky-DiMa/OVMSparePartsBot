from __future__ import annotations
from aiogram import types

from utils import RequestsTo1cService, morph
from classes.spare_part import SparePart
from classes.brand import Brand
from classes.redis_object import RedisObject
from classes.spare_part import SparePartStripped


class TooShortQueryException(Exception):
    """Query text is too short, the minimum length is 4."""
    pass


class SearchResult(RedisObject):
    redis_collection_name = "search_result"
    redis_TTL = 300
    redis_key = "text"
    fields = {"text": str, 'spare_parts': dict[str, list[SparePartStripped]], 'brands': dict[str, Brand]}
    def __init__(self, text: str, spare_parts: dict[str, list[SparePartStripped]], brands: dict[str, Brand]):
        self.text = text
        self.spare_parts = spare_parts
        self.brands = brands


    def __repr__(self) -> str:
        return f"{self.brands=}, {self.spare_parts=}"

    @property
    def brands_pages_count(self) -> int:
        return int(len(self.brands) // 10 + (1 if len(self.brands) % 10 > 0 else 0))

    @property
    def brands_list(self) -> list[Brand]:
        return list(self.brands.values())

    @property
    def brands_uids_list(self) -> list[str]:
        return list(self.brands.keys())

    def pages_count_of_brand(self, brand_n: int):
        spare_parts = self.spare_parts[self.brands_uids_list[brand_n]]
        return int(len(spare_parts) // 10 + (1 if len(spare_parts) % 10 > 0 else 0))

    def get_sp_page_of_brand(self, brand_n: int, n: int):
        spare_parts = sorted(self.spare_parts[self.brands_uids_list[brand_n]], reverse=True)
        return spare_parts[n * 10 : min((n + 1) * 10, len(spare_parts))]

    def get_brands_page(self, n: int) -> list[Brand]:
        return self.brands_list[n * 10 : min((n + 1) * 10, len(self.brands_list))]

    def brands_pages_keyboard(self, page_n: int) -> types.InlineKeyboardMarkup:
        inline_kb = []
        for i, brand in enumerate(self.get_brands_page(page_n)):
            inline_kb.append([types.InlineKeyboardButton(text=brand.name, callback_data=f'CHOOSE BRAND {page_n * 10 + i}')])
        if self.brands_pages_count > 1:
            inline_kb.append([types.InlineKeyboardButton(text='<<', callback_data=f'GOTO BRANDS PAGE {page_n - 1}'),
                              types.InlineKeyboardButton(text=f'{page_n + 1} / {self.brands_pages_count}',
                                                         callback_data=f'PAGE NUMBER {page_n + 1} {self.brands_pages_count}'),
                              types.InlineKeyboardButton(text='>>', callback_data=f'GOTO BRANDS PAGE {page_n + 1}')])
        inline_kb.append(
            [types.InlineKeyboardButton(text='Ввести другой запрос', callback_data='SEARCH AND DELETE CALL.MESSAGE')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    @staticmethod
    def get_page_n_by_item_n(item_n: int) -> int:
        return item_n // 10

    def sp_pages_of_brand_keyboard(self, brand_n: int, page_n: int) -> types.InlineKeyboardMarkup:
        inline_kb = []
        for i, sp in enumerate(self.get_sp_page_of_brand(brand_n, page_n)):
            inline_kb.append([types.InlineKeyboardButton(text=sp.name[:min(30, len(sp.name))] + ('...' if len(sp.name) > 30 else '') + f" ({sp.count} шт.)", callback_data=f'SHOW SP {brand_n} {page_n * 10 + i}')])
        if self.pages_count_of_brand(brand_n) > 1:
            inline_kb.append([
                types.InlineKeyboardButton(text='<<', callback_data=f'GOTO SP PAGE {page_n - 1} {brand_n}'),
                types.InlineKeyboardButton(text=f'{page_n + 1} / {self.pages_count_of_brand(brand_n)}',
                                           callback_data=f'PAGE NUMBER {page_n + 1} {self.pages_count_of_brand(brand_n)}'),
                types.InlineKeyboardButton(text='>>', callback_data=f'GOTO SP PAGE {page_n + 1} {brand_n}')])
        inline_kb.append([types.InlineKeyboardButton(text='<< НАЗАД >>',
                                                     callback_data=f'BACK TO BRANDS {self.get_page_n_by_item_n(brand_n)}')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    def __index_of_sp(self, code: str, brand_uid: str) -> int:
        for i, sp in enumerate(self.spare_parts):
            if sp.brand.uid == brand_uid and sp.code == code:
                return i
        return -1

    @classmethod
    async def get(cls, text: str) -> SearchResult:
        if len(text) < 4:
            raise TooShortQueryException(text)
        text = text.lower()
        redis_result = await cls.get_from_redis(text)
        if redis_result:
            return redis_result
        results_dicts = (await RequestsTo1cService.get_parts_by_text(text))["items"]
        code_sp = await SparePart.get_by_code(text)
        from classes.spare_part import SparePartStripped
        spare_parts: dict[str, list[SparePartStripped]] = {}
        all_brands = await Brand.get_all_brands_dict()
        brands: dict[str, Brand] = {}
        spare_part_added: dict[str, bool] = {}
        if code_sp:
            if not spare_parts.get(code_sp.brand.uid, []):
                spare_parts[code_sp.brand.uid] = []
            spare_parts.get(code_sp.brand.uid, []).append(code_sp.stripped)
            brands[code_sp.brand.uid] = code_sp.brand
            spare_part_added[code_sp.code] = True
        for spare_part_dict in results_dicts:
            brand = all_brands[spare_part_dict["brandid"]]
            spare_part_stripped = SparePartStripped(brand, spare_part_dict['name'], spare_part_dict['code'], int(spare_part_dict['count']) if spare_part_dict['count'] else 0)
            if not spare_part_added.get(spare_part_stripped.code, False):
                if not spare_parts.get(spare_part_stripped.brand.uid, []):
                    spare_parts[spare_part_stripped.brand.uid] = []
                spare_parts.get(spare_part_stripped.brand.uid, []).append(spare_part_stripped)
                spare_part_added[spare_part_stripped.code] = True
                brands[spare_part_stripped.brand.uid] = spare_part_stripped.brand
        for one_brand_spare_parts in spare_parts.values():
            one_brand_spare_parts.sort(reverse=True)
        self = cls(text, spare_parts, brands)
        await self.save_to_redis()
        return self

    @classmethod
    async def get_many(cls, texts: list[str]) -> list[SearchResult]:
        res: list[SearchResult] = []
        for text in texts:
            res.append(await cls.get(text))
        return res

    @classmethod
    async def get_many_in_dict(cls, texts: list[str]) -> dict[str, SearchResult]:
        res: dict[str, SearchResult] = {}
        for text in texts:
            res[text] = await cls.get(text)
        return res

    @property
    def spare_parts_count(self):
        return sum(map(lambda spare_parts: len(spare_parts), self.spare_parts.values()))

    def get_result_stats_text(self) -> str:
        return f'{"Найдена" if self.spare_parts_count == 0 else "Найдено"} <code>{self.spare_parts_count}</code> {morph.parse("запчасть")[0].make_agree_with_number(len(self.spare_parts)).word} <code>{len(self.brands)}</code> {morph.parse("бренд")[0].lexeme[1].make_agree_with_number(len(self.brands)).word}'

    def get_result_stats_text_for_brand(self, brand_n: int) -> str:
        count = len(self.spare_parts[self.brands_uids_list[brand_n]])
        return f'{"Найдена" if count == 0 else "Найдено"} <code>{count}</code> запчастей бренда <code>{self.brands_list[brand_n].name}</code>'
