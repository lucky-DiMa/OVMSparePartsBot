from __future__ import annotations
from copy import copy
from typing import List
from aiogram import types

from bot import requests_to_bd
from utils.setup_morphy import morph
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
    fields = {"text": str, 'spare_parts': list[SparePartStripped], 'brands': list[Brand]}
    def __init__(self, text: str, spare_parts: list[SparePartStripped], brands: list[Brand]):
        self.text = text
        self.spare_parts = spare_parts
        self.brands = brands

    # @property
    # def lower_text(self) -> str:
    #     return self.text.lower()

    def find_brand(self, uid: str) -> Brand | None:
        for brand in self.brands:
            if isinstance(brand, str):
                continue
            if brand.uid == uid:
                return copy(brand)
        return None

    def __brand_index(self, uid: str) -> int:
        for i, brand in enumerate(self.brands):
            if brand.uid == uid:
                return i
        return -1

    def filter_brand(self, uid: str):
        from .spare_part import SparePartStripped
        results: list | List[SparePartStripped] = []
        for sp in self.spare_parts:
            if sp.brand.uid == uid:
                results.append(copy(sp))
        return results

    def __repr__(self):
        return f"{self.brands=}, {self.spare_parts=}"

    @property
    def brands_pages_count(self):
        return int(len(self.brands) // 10 + (1 if len(self.brands) % 10 > 0 else 0))

    def pages_count_of_brand(self, brand_uid: str):
        spare_parts = self.filter_brand(brand_uid)
        return int(len(spare_parts) // 10 + (1 if len(spare_parts) % 10 > 0 else 0))

    def get_brands_page_n_by_uid(self, uid: str):
        brand_i = self.__brand_index(uid) + 1
        return int(brand_i // 10 + (1 if brand_i % 10 > 0 else 0))

    def get_sp_page_of_brand_by_n(self, brand_uid: str, n: int):
        page = []
        spare_parts = self.filter_brand(brand_uid)
        for i in range((n - 1) * 10, n * 10):
            if i >= len(spare_parts):
                break
            page.append(spare_parts[i])
        return page

    def get_brands_page_by_n(self, n: int):
        page = []
        for i in range((n - 1) * 10, n * 10):
            if i >= len(self.brands):
                break
            page.append(self.brands[i])
        return page

    def brands_pages_keyboard(self, page_n: int):
        inline_kb = []
        for brand in self.get_brands_page_by_n(page_n):
            inline_kb.append([types.InlineKeyboardButton(text=brand.name, callback_data=f'CHOOSE BRAND "{brand.uid}"')])
        if self.brands_pages_count > 1:
            inline_kb.append([types.InlineKeyboardButton(text='<<', callback_data=f'GOTO BRANDS PAGE {page_n - 1}'),
                              types.InlineKeyboardButton(text=f'{page_n} / {self.brands_pages_count}',
                                                         callback_data=f'PAGE NUMBER {page_n} {self.brands_pages_count}'),
                              types.InlineKeyboardButton(text='>>', callback_data=f'GOTO BRANDS PAGE {page_n + 1}')])
        inline_kb.append(
            [types.InlineKeyboardButton(text='Ввести другой запрос', callback_data='SEARCH AND DELETE CALL.MESSAGE')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    def sp_pages_of_brand_keyboard(self, brand_uid: str, page_n: int):
        inline_kb = []
        for sp in self.get_sp_page_of_brand_by_n(brand_uid, page_n):
            inline_kb.append([types.InlineKeyboardButton(text=sp.name[:min(20, len(sp.name))] + ('...' if len(sp.name) > 20 else ''), callback_data=f'SHOW SP {self.__index_of_sp(sp.code, sp.brand.uid)}')])
        if self.pages_count_of_brand(brand_uid) > 1:
            inline_kb.append([
                types.InlineKeyboardButton(text='<<', callback_data=f'GOTO SP PAGE {page_n - 1} "{brand_uid}"'),
                types.InlineKeyboardButton(text=f'{page_n} / {self.pages_count_of_brand(brand_uid)}',
                                           callback_data=f'PAGE NUMBER {page_n} {self.pages_count_of_brand(brand_uid)}'),
                types.InlineKeyboardButton(text='>>', callback_data=f'GOTO SP PAGE {page_n + 1} "{brand_uid}"')])
        inline_kb.append([types.InlineKeyboardButton(text='<< НАЗАД >>',
                                                     callback_data=f'BACK TO BRANDS {self.get_brands_page_n_by_uid(brand_uid)}')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    def get_spare_part(self, code: str):
        for spare_part in self.spare_parts:
            if spare_part.code == code:
                return spare_part
        return None

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
        results_dicts = requests_to_bd.get_parts_by_text(text)["items"]
        code_sp = await SparePart.get_by_code(text)
        from classes.spare_part import SparePartStripped
        spare_parts: list[SparePartStripped] = []
        all_brands = Brand.get_all_brands_dict()
        brands: list[Brand] = []
        brand_added: dict[str, bool] = {}
        spare_part_added: dict[str, bool] = {}
        if code_sp:
            spare_parts.append(code_sp.stripped)
            brands.append(code_sp.brand)
            brand_added[code_sp.brand.uid] = True
            brand_added[code_sp.code] = True
        for spare_part_dict in results_dicts:
            brand = all_brands[spare_part_dict["brandid"]]
            spare_part_stripped = SparePartStripped(brand, spare_part_dict['name'], spare_part_dict['code'])
            if not spare_part_added.get(spare_part_stripped.code, False):
                spare_parts.append(spare_part_stripped)
                spare_part_added[spare_part_stripped.code] = True
                if not brand_added.get(brand.uid, False):
                    brands.append(brand)
                    brand_added[brand.uid] = True
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

    def get_result_stats_text(self) -> str:
        return f'{"Найдена" if len(self.spare_parts) == 0 else "Найдено"} <code>{len(self.spare_parts)}</code> {morph.parse("запчасть")[0].make_agree_with_number(len(self.spare_parts)).word} <code>{len(self.brands)}</code> {morph.parse("бренд")[0].lexeme[1].make_agree_with_number(len(self.brands)).word}'

    def get_result_stats_text_for_brand(self, brand_uid: str) -> str:
        count = len(self.filter_brand(brand_uid))
        return f'{"Найдена" if count == 0 else "Найдено"} <code>{count}</code> запчастей бренда <code>{self.find_brand(brand_uid).name}</code>'
