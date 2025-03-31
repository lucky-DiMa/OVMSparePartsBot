from __future__ import annotations

import requests_to_bd
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
