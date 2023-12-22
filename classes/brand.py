from aiogram import types

from requests_to_bd import get_brands


class Brand:
    def __init__(self, uid: str, name: str):
        self.name = name
        self.uid = uid

    @classmethod
    def get_by_uid(cls, uid: str | None):
        for brands_dict in get_brands()["brands"]:
            if brands_dict["uid"] == uid:
                return cls(brands_dict["uid"], brands_dict["name"])
        return None

    @classmethod
    def get_page(cls, n: int):
        return [cls(brands_dict["uid"], brands_dict["name"]) for brands_dict in get_brands()["brands"][20*(n-1):20*n]]

    @classmethod
    def get_pages_keyboard(cls, page_n: int):
        inline_kb = []
        for brand in cls.get_page(page_n):
            inline_kb.append([types.InlineKeyboardButton(text=brand.name, callback_data=f'CHOOSE BRAND "{brand.uid}"')])
        if page_n == cls.pages_count:
            inline_kb.append([types.InlineKeyboardButton(text='Нужен другой бренд?', callback_data='NEED NEW BRAND')])
        inline_kb.append([types.InlineKeyboardButton(text='<<', callback_data=f'GOTO BRANDS PAGE {page_n - 1}'),
                          types.InlineKeyboardButton(text=f'{page_n} / {cls.pages_count()}', callback_data='BRANDS PAGE NUMBER'),
                          types.InlineKeyboardButton(text='>>', callback_data=f'GOTO BRANDS PAGE {page_n + 1}')])
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        return markup

    def __repr__(self):
        return f'{self.uid} {self.name}'

    @classmethod
    def pages_count(cls):
        return len(get_brands()["brands"]) // 20

    @classmethod
    def get_page_n(cls, uid: str):
        for i, brands_dict in enumerate(get_brands()["brands"]):
            if brands_dict["uid"] == uid:
                return (i // 20) + 1
        return -1


if __name__ == '__main__':
    print(Brand.get_by_uid(input()))
