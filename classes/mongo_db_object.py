from typing import ClassVar

from classes import JsonSerializableObject, classproperty
from mongo_connector import mongo_db


class MongoDBObject(JsonSerializableObject):
    collection_name: ClassVar[str]

    @classproperty
    @classmethod
    def collection(cls):
        return mongo_db[cls.collection_name]