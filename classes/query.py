from mongo_connector import mongo_db


class Query:
    def __init__(self, from_user_id: int, text: str, gmt_hour: int, gmt_minute: int):
        self.__from_user_id = from_user_id
        self.__text = text
        self.__gmt_hour = gmt_hour
        self.__gmt_minute = gmt_minute

    @property
    def from_user_id(self):
        """
        :rtype :int
        """
        return self.__from_user_id

    @property
    def text(self):
        """
        :rtype :str
        """
        return self.__text

    @property
    def gmt_hour(self):
        """
        :rtype :int
        """
        return self.__gmt_hour

    @property
    def gmt_minute(self):
        """
        :rtype :int
        """
        return self.__gmt_minute

    @classmethod
    def reg(cls, query):
        dict_query = {"from_user_id": query.from_user_id,
                      "text": query.text,
                      "gmt_hour": query.gmt_hour,
                      "gmt_minute": query.gmt_minute}
        mongo_db["Queries"].insert_one(dict_query)
        
    @staticmethod
    def delete_all():
        mongo_db["Queries"].drop()
        