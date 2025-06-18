from __future__ import annotations
from datetime import datetime, UTC
from classes.mongo_db_object import MongoDBObject
from classes.search_result import SearchResult




class SingleQuery(MongoDBObject):
    collection_name = 'Queries'
    fields = {'_id': int, 'from_user_id': int, 'text': str, 'datetime': datetime, "type": str}
    def __init__(self, _id: int,
                 from_user_id: int,
                 text: str,
                 _datetime: datetime,
                 type_: str = 'single'):
        self.__id = _id
        self.__from_user_id = from_user_id
        self.__text = text
        self.__datetime = _datetime
        self.__type = type_

    @property
    def from_user_id(self) -> int:
        return self.__from_user_id

    @property
    def _id(self) -> int:
        return self.__id

    @property
    def text(self) -> str:
        return self.__text

    @property
    def type(self) -> str:
        return self.__type

    @property
    def datetime(self) -> datetime:
        return self.__datetime

    async def get_result(self) -> SearchResult:
        return await SearchResult.get(self.text)

    @classmethod
    def create(cls, from_user_id: int, query_text: str, type_: str = 'single') -> SingleQuery:
        query = SingleQuery(cls.get_max_id() + 1, from_user_id, query_text, datetime.now(UTC), type_)
        cls.collection.insert_one(query.to_json())
        return cls.from_json(query.to_json())

    @classmethod
    def get_by_id(cls, _id: int) -> SingleQuery:
        return cls.from_json(cls.collection.find_one({"_id": _id}, cls.fields))

    @classmethod
    def delete_all(cls):
        cls.collection.drop()

    @classmethod
    def get_max_id(cls):
        try:
            return list(cls.collection.find({}, ['_id']).sort('_id', -1))[0]['_id']
        except IndexError:
            return -1

    @classmethod
    def get_all(cls) -> list[SingleQuery]:
        res = []
        for q_dict in cls.collection.find({}):
            res.append(cls.from_json(q_dict))
        return res

    def reload(self):
        pass

    @datetime.setter
    def datetime(self, _datetime: datetime):
        self.__datetime = _datetime
        self.__class__.collection.update_one({'_id': self._id}, {'$set': {'datetime': self.datetime}})


if __name__ == '__main__':
    SingleQuery.delete_all()
    print(datetime.utcnow())
