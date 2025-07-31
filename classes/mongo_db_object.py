from contextlib import contextmanager
from typing import ClassVar, Optional, Any, overload, Union

from bson import ObjectId
from pydantic import BaseModel, Field, PrivateAttr
from pymongo.collection import Collection

from classes.json_serializable_object import JsonSerializableObject
from classes.classproperty import classproperty
from classes.py_object_id import PyObjectId
from utils import mongo_db


class MongoDBModel(BaseModel):
    _collection_name: ClassVar[str]
    _collection: ClassVar[Collection]
    _auto_update: bool = PrivateAttr(True)

    object_id: Optional[PyObjectId] = Field(default=None, alias='_id', exclude=True)

    def __get_mongo_object_filter__(self):
        if not self.object_id:
            raise Exception('Object ID is not set')
        return {'_id': self.object_id}

    def _update(self, query: dict[str, Any]):
        self._update_one(self.__get_mongo_object_filter__(), query)

    @classmethod
    def _update_one(cls, _filter: dict[str, Any], update: dict[str, Any]):
        cls._collection.update_one(_filter, update)

    @classmethod
    def _update_many(cls, _filter: dict[str, Any], update: dict[str, Any]):
        cls._collection.update_many(_filter, update)


    @classproperty
    def _collection(cls) -> Collection:
        return mongo_db[cls._collection_name]

    @classmethod
    def get_one_from_mongo[T](cls: type[T], query_filter: dict) -> Optional[T]:
        data = cls._collection.find_one(query_filter)
        if data is None:
            return None
        return cls(**data)

    @classmethod
    def get_many_from_mongo[T](cls: type[T], query_filter: dict) -> list[T]:
        res = []
        for data in cls.collection.find(query_filter):
            res.append(cls(**data))
        return res

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if not name.startswith('_') and self._auto_update:
            self._set({name: value})

    @classmethod
    def insert_one[T: BaseModel](cls: type[T], data: T) -> T:
        data.id = cls.collection.insert_one(data.model_dump(by_alias=True, exclude={'id': True})).inserted_id
        return data

    def _set(self, data: dict[str, Any]) -> None:
        self._update_one(self.__get_mongo_object_filter__(), {'$set': data})

    @classmethod
    def _set_to_one(cls, _filter: dict[str, Any], data: dict[str, Any]):
        cls._update_one(_filter, {'$set': data})

    @classmethod
    def _set_to_many(cls, _filter: dict[str, Any], data: dict[str, Any]):
        cls._update_many(_filter, {'$set': data})

    def enable_auto_update(self):
        self._auto_update = True

    def disable_auto_update(self):
        self._auto_update = False

    def actualize(self):
        self._apply_instance(self.get_by_id(self.id))

    def save(self):
        self._set(self.model_dump())

    @contextmanager
    def paused_updates(self):
        old = self._auto_update
        self._auto_update = False
        try:
            yield self
        finally:
            self._auto_update = old

    def _apply_instance[T: MongoDBModel](self: T, another: T):
        with self.paused_updates():
            for field_name in self.model_fields.keys():
                setattr(self, field_name, getattr(another, field_name))

    def _generate_setitem_function(self, path: str):
        def setitem(self_dict, key: Any, value: Any):
            setitem(self_dict, key, value)
            if self._auto_update:
                self._set({f'{path}.{key}': value})
            if issubclass(type(value), dict):
                self._attach_auto_updates_to_dict(value, f'{path}.{key}')
        return setitem

    def model_post_init(self, __context: Any) -> None:
        for k in self.model_fields:
            if issubclass(type(getattr(self, k, None)), dict):
                self._attach_auto_updates_to_dict(getattr(self, k, None), k)

    def _attach_auto_updates_to_dict(self, d: dict, path: str):
        d.__setitem__ = self._generate_setitem_function(path)
        for k, v in d.items():
            if issubclass(type(v), dict):
                self._attach_auto_updates_to_dict(v, f'{path}.{k}')



    class Config:
        populate_by_name = True  # allow using "_id" instead of "id"
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }


if __name__ == '__main__':
    print(MongoDBModel().model_dump())