from typing import ClassVar

from json import loads, dumps
from classes.json_serializable_object import JsonSerializableObject
from utils import redis_client

class RedisObject(JsonSerializableObject):
    redis_collection_name: ClassVar[str]
    redis_key: ClassVar[str]
    redis_TTL: ClassVar[int]

    @classmethod
    async def get_from_redis[T](cls: type[T], key: str) -> T | None:
        json_result_string = await redis_client.get(f'{cls.redis_collection_name}:{key}')
        if not json_result_string:
            return None
        return cls.from_json(loads(json_result_string))

    async def save_to_redis(self) -> None:
        await redis_client.setex(f'{self.redis_collection_name}:{self.__getattribute__(self.redis_key)}', self.redis_TTL, dumps(self.to_json()))