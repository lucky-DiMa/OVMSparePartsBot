from __future__ import annotations

from aiogram.types import FSInputFile, InputMediaPhoto

from bot.create_bot import bot
from bot import requests_to_bd
from classes.user import User
from classes.json_serializable_object import JsonSerializableObject
from classes.photo import Photo
from classes.brand import Brand
from classes.redis_object import RedisObject


class Count(JsonSerializableObject):
    fields = {'count': int, 'warehouse_name': str}

    def __init__(self, count: int, warehouse_name: str):
        self.count = count
        self.warehouse_name = warehouse_name

    def __repr__(self):
        return f'{self.warehouse_name}: {self.count} шт.'

    def __str__(self):
        return f"{self.warehouse_name}: {self.count} шт."


class SparePart(RedisObject):
    redis_collection_name = 'spare_part'
    redis_key = 'code'
    redis_TTL = 300
    fields = {'brand': Brand, 'name': str, 'code': str, 'counts': list[Count],
              'photos': list[Photo]}

    def __init__(self, brand: Brand, name: str, code: str, counts: list[Count],
                 photos: list[Photo]):
        self.counts = counts
        self.brand = brand
        self.name = name
        self.photos = photos
        self.code = code

    @classmethod
    async def get_by_code(cls, code: str) -> SparePart | None:
        redis_result = await cls.get_from_redis(code)
        if redis_result:
            return redis_result
        result_dict = requests_to_bd.get_part_by_code(code)
        if result_dict['result'] in ['Товар или ячейка не найдены', 'Товар не найден']:
            return None
        result_dict = result_dict["item"]
        sp = cls(await Brand.get_by_uid(result_dict["brandid"]),
                   result_dict["name"],
                   result_dict["code"],
                   [Count(counts_dict["count"], counts_dict["namewh"]) for counts_dict in result_dict["counts"]],
                   [Photo(uid) for uid in result_dict["imgs"]])
        await sp.save_to_redis()
        return sp

    def __repr__(self):
        return f'{self.name=} {self.code=} {self.brand=} {self.counts=} {self.photos=} '

    @property
    def stripped(self):
        return SparePartStripped(self.brand, self.name, self.code)

    async def info_text(self) -> str:
        text = f'Артикул: <code>{self.code}</code>\nНаименование: <code>{self.name}</code>\nБренд: <code>{self.brand.name}</code>\n\n'
        if self.counts:
            text += 'В наличии:\n'
        else:
            text += 'Нет в наличии.\n'
        for count in self.counts:
            text += f"{count}\n"
        text += f'<a href="{await self.build_search_analogs_link()}">Искать аналоги</a>'
        return text

    async def export_images_to_telegram_media(self) -> list[InputMediaPhoto] | FSInputFile | None:
        if len(self.photos) == 1:
            return FSInputFile(self.photos[0].download())
        elif len(self.photos) == 0:
            return None
        else:
            media_list = []
            for i, photo in enumerate(self.photos):
                if i == 0:
                    media_list.append(
                        InputMediaPhoto(media=FSInputFile(photo.download()), caption=await self.info_text(),
                                              parse_mode='HTML'))
                    continue
                media_list.append(InputMediaPhoto(media=FSInputFile(photo.download())))
            return media_list

    def remove_all_photos(self):
        for photo in self.photos:
            photo.remove()

    async def send_info_to_user(self, user: User) -> None:
        try:
            payload = await self.export_images_to_telegram_media()
            if not payload:
                await user.send_message(await self.info_text())
            elif isinstance(payload, FSInputFile):
                await user.send_photo(payload, caption=await self.info_text())
            else:
                await user.send_media_group(payload)
        except Exception:
            await user.send_message(await self.info_text() + "\n\nПроизошла ошибка при загрузке изображений.")
        finally:
            self.remove_all_photos()

    async def build_search_analogs_link(self) -> str:
        return f'https://t.me/{(await bot.me()).username}?start=search-analogs--{self.code.replace(" ", "---space---")}'


class SparePartStripped(JsonSerializableObject):
    fields = {'brand': Brand, 'name': str, 'code': str}

    def __init__(self, brand: Brand, name: str, code: str,):
        self.brand = brand
        self.name = name
        self.code = code

    async def get_full_info(self) -> SparePart:
        return await SparePart.get_by_code(self.code)

    def __repr__(self):
        return f'{self.name=} {self.code=} {self.brand=} '


if __name__ == '__main__':
    pass
