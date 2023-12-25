from datetime import datetime

from classes.spare_part import SparePart
from classes.json_serializable_class import JsonSerializableClass
from classes.search_result import SearchResult
from mongo_connector import mongo_db


class Query(JsonSerializableClass):
    __cluster = mongo_db["Queries"]

    def __init__(self, _id: int,
                 from_user_id: int,
                 message_id: int,
                 text: str,
                 _datetime: datetime,
                 result: SearchResult):
        self.__id = _id
        self.__message_id = message_id
        self.__from_user_id = from_user_id
        self.__text = text
        self.__datetime = _datetime
        self.__result = result

    @property
    def from_user_id(self):
        """
        :rtype :int
        """
        return self.__from_user_id

    @property
    def id(self):
        """
        :rtype :int
        """
        return self.__id

    @property
    def message_id(self):
        """
        :rtype :int
        """
        return self.__message_id

    @property
    def text(self):
        """
        :rtype :str
        """
        return self.__text

    @property
    def datetime(self):
        """
        :rtype :datetime
        """
        return self.__datetime

    @property
    def result(self) -> SearchResult:
        return self.__result

    @message_id.setter
    def message_id(self, _message_id: int):
        self.__message_id = _message_id
        self.__class__.__cluster.update_one({'_id', self.id}, {"$set": {"message_id": self.message_id}})

    @result.setter
    def result(self, _result: SearchResult):
        self.__result = _result
        self.__class__.__cluster.update_one({'_id': self.id}, {"$set": {"result": self.result.to_JSON()}})

    @classmethod
    def make_new(cls, from_user_id: int, query: str, message_id: int):
        result = SparePart.search(query)
        dict_query = {"_id": cls.get_max_id() + 1,
                      "from_user_id": from_user_id,
                      "message_id": message_id,
                      "text": query,
                      "datetime": str(datetime.utcnow()),
                      "result": result.to_JSON()}
        cls.__cluster.insert_one(dict_query)
        return cls.from_JSON(dict_query)

    @classmethod
    def get_by_id(cls, _id: int):
        pass

    @classmethod
    def delete_all(cls):
        cls.__cluster.drop()

    @classmethod
    def get_max_id(cls):
        try:
            return list(cls.__cluster.find({}, ['_id']).sort('_id', -1))[0]['_id']
        except IndexError:
            return -1

    @classmethod
    def from_JSON(cls, dict_query: dict):
        return cls(dict_query['_id'],
                   dict_query['from_user_id'],
                   dict_query['message_id'],
                   dict_query['text'],
                   datetime.strptime(dict_query['datetime'], "%Y-%m-%d %H:%M:%S.%f"),
                   SearchResult.from_JSON(dict_query['result']))

    @classmethod
    def get_by_from_user_id_and_message_id(cls, from_user_id: int, message_id: int):
        return cls.from_JSON(cls.__cluster.find_one({"from_user_id": from_user_id, "message_id": message_id}))

if __name__ == '__main__':
    Query.delete_all()
    print(datetime.utcnow())
