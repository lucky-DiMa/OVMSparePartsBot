from typing import List

from aiogram import types

from classes.brand import Brand


class NoBrandSearchResult:
    def __init__(self, spare_parts: List[dict]):
        self.brands = []
        self.spare_parts_count = len(spare_parts)
        for spare_part in spare_parts:
            if spare_part["brandid"] not in self.brands:
                self.brands.append(spare_part["brandid"])

    # @property
    # def sp_pages_count(self):
    #     return int(len(self.spare_parts) // 10 + (1 if len(self.spare_parts) % 10 > 0 else 0))

    @property
    def brands_pages_count(self):
        return int(len(self.brands) // 10 + (1 if len(self.brands) % 10 > 0 else 0))

    def get_brands_page_n_by_uid(self, uid: str):
        brand_i = self.brands.index(uid) + 1
        return int(brand_i // 10 + (1 if brand_i % 10 > 0 else 0))

    def get_brands_page_by_n(self, n: int):
        from classes.brand import Brand
        page = []
        for i in range((n-1)*10, n*10):
            if i >= len(self.brands):
                break
            page.append(Brand.get_by_uid(self.brands[i]))
        return page

    def brands_pages_keyboard(self, page_n: int):
        inline_kb = []
        for brand in self.get_brands_page_by_n(page_n):
            inline_kb.append([types.InlineKeyboardButton(text=brand.name, callback_data=f'CHOOSE BRAND "{brand.uid}"')])
        if self.brands_pages_count > 1:
            inline_kb.append([types.InlineKeyboardButton(text='<<', callback_data=f'GOTO BRANDS PAGE {page_n - 1}'),
                              types.InlineKeyboardButton(text=f'{page_n} / {self.brands_pages_count}', callback_data=f'PAGE NUMBER {page_n} {self.brands_pages_count}'),
                              types.InlineKeyboardButton(text='>>', callback_data=f'GOTO BRANDS PAGE {page_n + 1}')])
        inline_kb.append([types.InlineKeyboardButton(text='Ввести другой запрос', callback_data=f'SEARCH AND DELETE CALL.MESSAGE')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup


class BrandSearchResult:
    def __init__(self, query: str, spare_parts: List[dict], brand_uid: str):
        self.query = query
        self.spare_parts = spare_parts
        self.brand = Brand.get_by_uid(brand_uid)

    def get_sp_page(self, n):
        from classes.spare_part import SparePart
        page = []
        for i in range((n-1)*10, n*10):
            if i >= len(self.spare_parts):
                break
            page.append(SparePart.get_by_article(self.spare_parts[i]["code"], self.brand.uid))
        return page

    def sp_pages_keyboard(self, page_n: int):
        inline_kb = []
        for sp in self.get_sp_page(page_n):
            inline_kb.append([types.InlineKeyboardButton(text=sp.naming, callback_data=f'SHOW {sp.article} "{sp.brand.uid}"')])
        if self.sp_pages_count > 1:
            inline_kb.append([types.InlineKeyboardButton(text='<<', callback_data=f'GOTO SP PAGE {page_n - 1} "{self.brand.uid}"'),
                              types.InlineKeyboardButton(text=f'{page_n} / {self.sp_pages_count}', callback_data=f'PAGE NUMBER {page_n} {self.sp_pages_count}'),
                              types.InlineKeyboardButton(text='>>', callback_data=f'GOTO SP PAGE {page_n + 1} "{self.brand.uid}"')])
        from classes.spare_part import SparePart
        inline_kb.append([types.InlineKeyboardButton(text='<< НАЗАД >>',
                                              callback_data=f'BACK TO BRANDS {SparePart.search(self.query).get_brands_page_n_by_uid(self.brand.uid)}')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    @property
    def sp_pages_count(self):
        return int(len(self.spare_parts) // 10 + (1 if len(self.spare_parts) % 10 > 0 else 0))


