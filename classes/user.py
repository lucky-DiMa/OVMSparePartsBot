from mongo_connector import mongo_db


class User:
    def __init__(self, tg_id: int, phone: str = '',
                 state: str = 'NONE',
                 id_of_message_promoter_to_type: int = -1,
                 text_of_message_promoter_to_type:str = '',
                 previous_query: str = ''):
        self.__id = tg_id
        self.__phone = phone
        self.__state = state
        self.__id_of_message_promoter_to_type = id_of_message_promoter_to_type
        self.__text_of_message_promoter_to_type = text_of_message_promoter_to_type
        self.__previous_query = previous_query

    @property
    def id(self):
        return self.__id

    @property
    def phone(self):
        return self.__phone

    @property
    def state(self):
        return self.__state

    @property
    def id_of_message_promoter_to_type(self):
        return self.__id_of_message_promoter_to_type

    @property
    def text_of_message_promoter_to_type(self):
        return self.__text_of_message_promoter_to_type

    @property
    def previous_query(self):
        return self.__previous_query

    @property
    def end_type_text(self):
        return "NONE" if self.state == 'NONE' else 'Сначала отправьте поисковой запрос!' if self.state == "TYPING QUERY" else "Сначала отправьте сообщение обратной связи!" if self.state == 'TYPING FEEDBACK' else 'Сначала поделитесь своим контактом!'

    @phone.setter
    def phone(self, phone: str):
        self.__phone = phone
        mongo_db["Users"].update_one({"id": self.id}, {"$set": {"phone": phone}})

    @state.setter
    def state(self, state: str):
        self.__state = state
        mongo_db["Users"].update_one({"id": self.id}, {"$set": {"state": state}})

    @id_of_message_promoter_to_type.setter
    def id_of_message_promoter_to_type(self, id_of_message_promoter_to_type: str):
        self.__id_of_message_promoter_to_type = id_of_message_promoter_to_type
        mongo_db["Users"].update_one({"id": self.id}, {"$set": {"id_of_message_promoter_to_type": id_of_message_promoter_to_type}})

    @text_of_message_promoter_to_type.setter
    def text_of_message_promoter_to_type(self, text_of_message_promoter_to_type: str):
        self.__text_of_message_promoter_to_type = text_of_message_promoter_to_type
        mongo_db["Users"].update_one({"id": self.id}, {"$set": {"text_of_message_promoter_to_type": text_of_message_promoter_to_type}})

    @previous_query.setter
    def previous_query(self, previous_query: str):
        self.__previous_query = previous_query
        mongo_db["Users"].update_one({"id": self.id}, {"$set": {"previous_query": previous_query}})

    @classmethod
    def reg(cls, tg_id: int):
        """
        :rtype :User
        """
        if cls.get_by_id(tg_id) is None:
            new_user = User(tg_id)
            mongo_db["Users"].insert_one({"id": new_user.id,
                                          "phone": new_user.phone,
                                          "state": new_user.state,
                                          "id_of_message_promoter_to_type": new_user.id_of_message_promoter_to_type,
                                          "text_of_message_promoter_to_type": new_user.text_of_message_promoter_to_type,
                                          "previous_query": new_user.previous_query})
        return cls.get_by_id(tg_id)

    @classmethod
    def get_by_id(cls, tg_id: int):
        """
        :rtype :User
        """
        user_dict = mongo_db["Users"].find_one({"id": tg_id})
        if user_dict is None:
            return None
        return cls(user_dict["id"],
                    user_dict["phone"],
                    user_dict["state"],
                    user_dict["id_of_message_promoter_to_type"],
                    user_dict["text_of_message_promoter_to_type"],
                    user_dict["previous_query"])

    @classmethod
    def del_by_id(cls, tg_id: int):
        mongo_db["Users"].delete_one({"id": tg_id})
        
    @staticmethod
    def delete_all():
        mongo_db["Users"].drop()

    @classmethod
    def exists_by_id(cls, tg_id: int):
        return mongo_db["Users"].find_one({"id": tg_id}, ["id"]) is not None
    