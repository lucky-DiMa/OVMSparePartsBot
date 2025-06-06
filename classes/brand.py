from __future__ import annotations
from classes.redis_object import RedisObject
from bot.requests_to_bd import get_brands

class Brand(RedisObject):
    redis_collection_name = 'Brands'
    redis_key = 'uid'
    redis_TTL = 300
    fields = {'uid': str, 'name': str}
    def __init__(self, uid: str, name: str):
        self.name = name
        self.uid = uid

    @classmethod
    async def get_by_uid(cls, uid: str | None) -> Brand | None:
        redis_result = await cls.get_from_redis(uid)
        if redis_result:
            return redis_result
        for brands_dict in get_brands()["brands"]:
            if brands_dict["uid"] == uid:
                self = cls.from_json(brands_dict)
                await self.save_to_redis()
                return self
        return None

    @classmethod
    def get_all_brands_dict(cls) -> dict[str, Brand]:
        result: dict[str, Brand] = {}
        for brands_dict in get_brands()["brands"]:
            result[brands_dict["uid"]] = Brand.from_json(brands_dict)
        return result

    def __repr__(self):
        return f'{self.uid} {self.name}'


if __name__ == '__main__':
    print(Brand.from_json(Brand('abc', 'abc-name').to_json()).to_json())
