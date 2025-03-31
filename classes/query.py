from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, UTC
from aiogram import types

from classes.json_serializable_object import JsonSerializableObject
from classes.search_result import SearchResult
from mongo_connector import mongo_db

query_type_name = {"single": 'обычный',
                   "multi": "мульти"}


def get_query_type(message: types.Message):
    if len(message.reply_markup.inline_keyboard) < 2:
        return None
    return message.reply_markup.inline_keyboard[0][0].callback_data.split()[-1]


class Query(JsonSerializableObject):
    collection_name = 'Queries'
    collection = mongo_db[collection_name]
    fields = {'_id': int, 'from_user_id': int, 'message_id': int, 'text': str, 'datetime': datetime, "type": str}
    def __init__(self, _id: int,
                 from_user_id: int,
                 message_id: int,
                 text: str,
                 _datetime: datetime,
                 type_: str = 'single'):
        self.__id = _id
        self.__message_id = message_id
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
    def message_id(self) -> int:
        return self.__message_id

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

    @message_id.setter
    def message_id(self, _message_id: int):
        self.__message_id = _message_id
        self.__class__.collection.update_one({'_id', self._id}, {"$set": {"message_id": self.message_id}})

    @classmethod
    def create(cls, from_user_id: int, query_text: str, message_id: int, type_: str = 'single'):
        query = Query(cls.get_max_id() + 1, from_user_id, message_id, query_text, datetime.now(UTC), type_)
        cls.collection.insert_one(query.to_JSON())
        return cls.from_JSON(query.to_JSON())

    @classmethod
    def get_by_id(cls, _id: int):
        return cls.from_JSON(cls.collection.find_one({"_id": _id}, cls.fields))

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
    def get_by_from_user_id_and_message_id(cls, from_user_id: int, message_id: int):
        return cls.from_JSON(cls.collection.find_one({"from_user_id": from_user_id, "message_id": message_id}, cls.fields_keys))

    @property
    def expiration_datetime(self):
        return self.datetime + timedelta(minutes=5)

    @classmethod
    def get_all(cls):
        res = []
        for q_dict in cls.collection.find({}):
            res.append(cls.from_JSON(q_dict))
        return res

    def reload(self):
        pass

    @datetime.setter
    def datetime(self, _datetime: datetime):
        self.__datetime = _datetime
        self.__class__.collection.update_one({'_id': self._id}, {'$set': {'datetime': self.datetime}})


if __name__ == '__main__':
    Query.delete_all()
    print(datetime.utcnow())
