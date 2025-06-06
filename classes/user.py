from __future__ import annotations

from aiogram import types

from classes.mongo_db_object import MongoDBObject
from config import MANUAL_URL
from bot import bot


class User(MongoDBObject):
    fields = {"id": int, "phone": str, "state": str, "id_of_message_promoter_to_type": str, 'text_of_message_promoter_to_type': str,
              'previous_query': str}
    collection_name = 'Users'

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
        self.collection.update_one({"id": self.id}, {"$set": {"phone": phone}})

    @state.setter
    def state(self, state: str):
        self.__state = state
        self.collection.update_one({"id": self.id}, {"$set": {"state": state}})

    @id_of_message_promoter_to_type.setter
    def id_of_message_promoter_to_type(self, id_of_message_promoter_to_type: str):
        self.__id_of_message_promoter_to_type = id_of_message_promoter_to_type
        self.collection.update_one({"id": self.id}, {"$set": {"id_of_message_promoter_to_type": id_of_message_promoter_to_type}})

    @text_of_message_promoter_to_type.setter
    def text_of_message_promoter_to_type(self, text_of_message_promoter_to_type: str):
        self.__text_of_message_promoter_to_type = text_of_message_promoter_to_type
        self.collection.update_one({"id": self.id}, {"$set": {"text_of_message_promoter_to_type": text_of_message_promoter_to_type}})

    @previous_query.setter
    def previous_query(self, previous_query: str):
        self.__previous_query = previous_query
        self.collection.update_one({"id": self.id}, {"$set": {"previous_query": previous_query}})

    @classmethod
    def reg(cls, tg_id: int) -> User:
        if (user := cls.get_by_id(tg_id)) is None:
            user = User(tg_id)
            cls.collection.insert_one(user.to_json())
            return user
        return user

    @classmethod
    def get_by_id(cls, tg_id: int) -> User | None:
        user_dict = cls.collection.find_one({"id": tg_id})
        if user_dict is None:
            return None
        return cls.from_json(user_dict)

    def delete(self):
        self.__class__.delete_by_id(self.id)

    @classmethod
    def delete_by_id(cls, tg_id: int):
        cls.collection.delete_one({"id": tg_id})
        
    @classmethod
    def delete_all(cls):
        cls.collection.drop()

    @classmethod
    def exists_by_id(cls, tg_id: int):
        return cls.collection.find_one({"id": tg_id}) is not None

    @property
    def help_message_text(self) -> str:
        text = 'Вот список команд доступных для вас:'
        from bot.commands import commands
        for command_name, command_info in commands.items():
                text += f'\n{command_name} - {command_info.explanation}'
        text += f'\n\nНужна помощь? Прочитайте наше <a href="{MANUAL_URL}">руководство пользования</a>.'
        return text

    async def send_message(self, text: str, reply_to_message_id: int | None = None,
                           markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None) -> types.Message:
            return await bot.send_message(self.id, text, reply_to_message_id=reply_to_message_id, reply_markup=markup,
                                          parse_mode='HTML')

    async def send_photo(self, document: types.FSInputFile | types.URLInputFile, caption:  str, reply_to_message_id: int | None = None, reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None):
        await bot.send_photo(self.id, document, caption=caption, parse_mode="HTML", reply_markup=reply_markup,
                             reply_to_message_id=reply_to_message_id)

    async def send_video(self, document: types.FSInputFile | types.URLInputFile, caption:  str, reply_to_message_id: int | None = None, reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None):
        await bot.send_video(self.id, document, caption=caption, parse_mode="HTML", reply_markup=reply_markup,
                             reply_to_message_id=reply_to_message_id)

    async def send_audio(self, document: types.FSInputFile | types.URLInputFile, caption:  str, reply_to_message_id: int | None = None, reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None):
        await bot.send_audio(self.id, document, caption=caption, parse_mode="HTML", reply_markup=reply_markup,
                             reply_to_message_id=reply_to_message_id)

    async def send_document(self, document: types.FSInputFile | types.URLInputFile, caption:  str, reply_to_message_id: int | None = None, reply_markup: types.InlineKeyboardMarkup | types.ReplyKeyboardMarkup | None = None):
        await bot.send_document(self.id, document, caption=caption, parse_mode="HTML", reply_markup=reply_markup,
                                reply_to_message_id=reply_to_message_id)

    async def send_media_group(self, media_list: list[types.InputMediaAudio | types.InputMediaDocument | types.InputMediaPhoto | types.InputMediaVideo], reply_to_message_id: int | None = None):
        await bot.send_media_group(self.id, media_list,
                                   reply_to_message_id=reply_to_message_id)