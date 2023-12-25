from copy import copy
from typing import List
from aiogram import types
from icecream import ic
from .brand import Brand
from .json_serializable_class import JsonSerializableClass


class SearchResult(JsonSerializableClass):
    def __init__(self, spare_parts: List[dict], brands: List[dict] | None = None):
        # ic.enable()
        self.brands: list | List[str, Brand] = []
        if brands is None:
            for spare_part in spare_parts:
                if spare_part["brandid"] not in self.brands:
                    self.brands.append(spare_part["brandid"])
            ic('GETTING BRANDS')
            for i, b_uid in enumerate(self.brands):
                self.brands[i] = Brand.get_by_uid(b_uid)
        else:
            for brand_dict in brands:
                self.brands.append(Brand.from_JSON(brand_dict))
        from .spare_part import SparePartStripped
        self.spare_parts: list | List[SparePartStripped] = []
        from .spare_part import SparePartStripped
        ic('MY CODE STARTED')
        for sp_dict in spare_parts:
            if "brandid" in  sp_dict.keys():
                sp_dict["brand"] = self.find_brand(sp_dict["brandid"]).to_JSON()
                sp_dict.pop("brandid")
            self.spare_parts.append(SparePartStripped.from_JSON(sp_dict))
        # ic.disable()

    @classmethod
    def from_JSON(cls, json_dict: dict):
        return cls(**json_dict)

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
            [types.InlineKeyboardButton(text='Ввести другой запрос', callback_data=f'SEARCH AND DELETE CALL.MESSAGE')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    def sp_pages_of_brand_keyboard(self, brand_uid: str, page_n: int):
        inline_kb = []
        for sp in self.get_sp_page_of_brand_by_n(brand_uid, page_n):
            inline_kb.append([types.InlineKeyboardButton(text=sp.name, callback_data=f'SHOW {sp.code} "{sp.brand.uid}"')])
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
