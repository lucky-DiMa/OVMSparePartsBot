from __future__ import annotations

from typing import NamedTuple, AnyStr, Any

from aiogram import types

from bot.admin_permissions import permissions
from classes.states import State, States
from classes.mongo_db_object import MongoDBObject
from config import MANUAL_URL
from bot import bot
from utils import mongo_db


class IsEditingResult(NamedTuple):
    is_editing: bool
    who_is_editing: User | None


class UserNotFoundException(Exception):
    """User with given id not found"""


class AlreadyDoneException(Exception):
    """Action already done"""


class AdminAlreadyPromotedException(AlreadyDoneException):
    """User already is admin"""


class AdminAlreadyDismissedException(AlreadyDoneException):
    """User already is not admin"""


class PermissionDeniedException(Exception):
    """Permission denied"""


class UserNotRegisteredException(Exception):
    """User not registered"""


class PermissionAlreadyAllowedException(AlreadyDoneException):
    """Permission already allowed"""


class CantEditAdminPermissionOfNonAdminUserException(Exception):
    """Can't edit permission of non-admin user"""


class PermissionAlreadyRestrictedException(AlreadyDoneException):
    """Permission already restricted"""


class BannedUserNotFoundException(Exception):
    """Banned User with given id not found"""

class User(MongoDBObject):
    fields = {"id": int, 'is_owner': bool, 'is_admin': bool, "phone": str, "state": str, "id_of_message_promoter_to_type": str, 'text_of_message_promoter_to_type': str,
              'previous_query': str, 'admin_permissions': dict[str, bool]}
    collection_name = 'Users'
    
    full_admin_permissions = {permission_name: True for permission_name in permissions.keys()}
    default_admin_permissions = {permission_name: False for permission_name in permissions.keys()}

    def __init__(self, tg_id: int,
                 is_owner: bool = False,
                 is_admin: bool = False,
                 phone: str = '',
                 state: str = State(States.JUST_STARTED).serialization,
                 id_of_message_promoter_to_type: int = -1,
                 text_of_message_promoter_to_type:str = '',
                 previous_query: str = '',
                 admin_permissions: dict[str, bool] = None):
        self.__is_admin = is_admin
        self.__is_owner = is_owner
        if admin_permissions is None:
            admin_permissions = {}
        self.__id = tg_id
        self.__phone = phone
        self.__state = state
        self.__id_of_message_promoter_to_type = id_of_message_promoter_to_type
        self.__text_of_message_promoter_to_type = text_of_message_promoter_to_type
        self.__previous_query = previous_query
        self.__admin_permissions = admin_permissions

    @property
    def id(self) -> int:
        return self.__id

    @property
    def phone(self) -> str:
        return self.__phone

    @property
    def state(self) -> str:
        return self.__state

    @property
    def parsed_state(self) -> State:
        return State.parse(self.state)

    @property
    def admin_permissions(self) ->  dict[str, bool]:
        return self.__admin_permissions

    @property
    def id_of_message_promoter_to_type(self) -> int:
        return self.__id_of_message_promoter_to_type

    @property
    def text_of_message_promoter_to_type(self) -> str:
        return self.__text_of_message_promoter_to_type

    @property
    def previous_query(self) -> str:
        return self.__previous_query

    @property
    def is_owner(self) -> bool:
        return self.__is_owner

    @property
    def is_admin(self) -> bool:
        return self.__is_admin

    @property
    def end_type_text(self) -> str:
        return "NONE" if self.state == 'NONE' else 'Сначала отправьте поисковой запрос!' if self.state == "TYPING QUERY" else "Сначала отправьте сообщение обратной связи!" if self.state == 'TYPING FEEDBACK' else 'Сначала поделитесь своим контактом!'

    @phone.setter
    def phone(self, phone: str):
        self.__phone = phone
        self.collection.update_one({"id": self.id}, {"$set": {"phone": phone}})

    @state.setter
    def state(self, state: str):
        self.__state = state
        self.collection.update_one({"id": self.id}, {"$set": {"state": state}})

    def set_state(self, state: States, target: int | str = None):
        self.state = State(state, str(target) if target else None).serialization

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

    def is_allowed(self, permission_name: str):
        return self.is_owner or (self.is_admin and self.__admin_permissions[permission_name])

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

    @is_admin.setter
    def is_admin(self, is_admin: bool):
        if self.__is_admin is is_admin:
            raise AdminAlreadyPromotedException(
                f'User: {self.id}') if is_admin else AdminAlreadyDismissedException(
                f'User: {self.id}')
        self.__set_field("is_admin", is_admin)
        self.__set_field('admin_permissions', self.__class__.default_admin_permissions)
        self.__is_admin = is_admin

    def get_info(self, for_myself: bool = False) -> str:
        text = f'Пользователь <code>{self.id}</code>{"(Вы)" if for_myself else""}:\n\nТелефон: <code>{self.phone}</code>\nСтатус: {self.parsed_state.explanation}\nАдмин: {"✅" if self.is_admin else "❌"}' + (
            f'\n\nПрава админа:' if self.is_admin else '')
        if self.is_admin:
            for permission_name, permission_text in permissions.items():
                text += f'\n{permission_text} - {"✅" if self.admin_permissions.get(permission_name, False) else "❌"}'
        if self.is_owner:
            text += '\n<tg-spoiler>Абсолютные права: ✅</tg-spoiler>'
        return text

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

    def allow_permission(self, user_id: int, permission_name: str):
        if not self.is_owner:
            if not self.is_admin:
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is not admin.')
            if not self.is_allowed('choose_admins'):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin but have not this permission')
            if not self.is_higher(user_id):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is lower than user {user_id}')
            if permission_name == 'choose_admins':
                raise PermissionDeniedException(f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is not owner and can not allow someone to choose admins.')
        user = User.get_by_id(user_id)
        if not user.is_admin:
            raise CantEditAdminPermissionOfNonAdminUserException(f'User: "{user.fullname}" {user.id}')
        if user.is_allowed(permission_name):
            raise PermissionAlreadyAllowedException(f'User: {user_id}. Permission: {permission_name}.')
        if permission_name == 'choose_admins':
            self.__set_field_by_id(user_id, "admin_permissions", self.__class__.full_admin_permissions)
        else:
            self.__set_field_by_id(user_id, f"admin_permissions.{permission_name}", True)

    def restrict_permission(self, user_id: int, permission_name: str):
        if not self.is_owner:
            if not self.is_admin:
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is not admin.')
            if not self.is_allowed('choose_admins'):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin but have not this permission')
            if not self.is_higher(user_id):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: /ban. Reason: user is admin and have this permission but he is lower than user {user_id}')
            if permission_name == 'choose_admins':
                raise PermissionDeniedException(f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is not owner and can not allow someone to choose admins.')
        user = User.get_by_id(user_id)
        if not user.is_admin:
            raise CantEditAdminPermissionOfNonAdminUserException(f'User: "{user.fullname}" {user.id}')
        if not user.is_allowed(permission_name):
            raise PermissionAlreadyRestrictedException(f'User: {user_id}. Permission: {permission_name}.')
        if permission_name != 'choose_admins':
            self.__class__.__set_field_by_id(user_id, "admin_permissions.choose_admins", False)
        self.__class__.__set_field_by_id(user_id, f"admin_permissions.{permission_name}", False)

    def is_higher(self, user_id: int) -> bool:
        user = User.get_by_id(user_id)
        return self.is_owner or (
               self.is_allowed('choose_admins') and not user.is_allowed('choose_admins')) or (
               self.is_admin and not user.is_admin)
    
    #TODO
    # def ban(self, user_id: int):
    #     if not self.is_owner:
    #         if not self.is_admin:
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /ban. Reason: user is not admin.')
    #         if not self.is_allowed('/ban'):
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /ban. Reason: user is admin but have not this permission')
    #         if not self.is_higher(user_id):
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /ban. Reason: user is admin and have this permission but he is lower than user {user_id}')
    #     self.__class__.ban_by_id(user_id)
    
    #TODO
    # def kick(self, user_id: int):
    #     if not self.is_owner:
    #         if not self.is_admin:
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /kick. Reason: user is not admin.')
    #         if not self.is_allowed('/kick'):
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /kick. Reason: user have not this permission')
    #         if not self.is_higher(user_id):
    #             raise PermissionDeniedException(
    #                 f'User: {self.id}. Permission: /kick. Reason: user is admin and have this permission but he is lower than user {user_id}')
    #     self.__class__.delete_by_id(user_id)

    @classmethod
    def registered_by_id(cls, user_id: int) -> bool:
        #TODO
        if not cls.exists_by_id(user_id):
            return False
        return cls.get_by_id(user_id).state not in ['CHOOSING LOCATION', 'CHOOSING SECTION', 'TYPING FULLNAME',
                                                    'WAITING FOR REG CONFIRMATION']

    def registered(self) -> bool:
        #TODO
        return self.state not in ['CHOOSING LOCATION', 'CHOOSING SECTION', 'TYPING FULLNAME',
                                  'WAITING FOR REG CONFIRMATION']

    def promote_to_admin(self, user_id: int):
        if not self.__class__.registered_by_id(user_id):
            raise UserNotRegisteredException(f'User: "{user_id}.')
        if not self.is_owner:
            if not self.is_admin:
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is not admin.')
            if not self.is_allowed('choose_admins'):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin but have not this permission')
            if not self.is_higher(user_id):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is lower than user {user_id}')
        user = self.__class__.get_by_id(user_id)
        user.is_admin = True

    def dismiss_admin(self, user_id: int):
        if not self.__class__.registered_by_id(user_id):
            raise UserNotRegisteredException(f'User: "{user_id}.')
        if not self.is_owner:
            if not self.is_admin:
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is not admin.')
            if not self.is_allowed('choose_admins'):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin but have not this permission')
            if not self.is_higher(user_id):
                raise PermissionDeniedException(
                    f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is lower than user {user_id}')
        user = self.__class__.get_by_id(user_id)
        user.is_admin = False

    def __set_field(self, field: str, value: Any):
        self.collection.update_one({'id': self.id}, {'$set': {field: value}})

    @classmethod
    def __set_field_by_id(cls, _id: int, field: str, value: Any):
        cls.collection.update_one({"id": _id}, {"$set": {field: value}})

    @classmethod
    def ban_by_id(cls, tg_id: int):
        phone = 'Не известно'
        if cls.is_banned_by_id(tg_id):
            raise AlreadyDoneException(f'User: {tg_id} already banned!')
        try:
            ban_user = cls.get_by_id(tg_id)
            if ban_user.phone != 'NONE':
                phone = ban_user.phone
        except UserNotFoundException as exception:
            raise exception
        finally:
            mongo_db["BannedUsers"].insert_one({"id": tg_id, "phone": phone})
            cls.delete_by_id(tg_id)

    @classmethod
    def is_banned_by_id(cls, tg_id: int) -> bool:
        if mongo_db["BannedUsers"].find_one({"id": tg_id}):
            return True
        return False

    @classmethod
    def get_responders(cls) -> list[User] | list:
        return list(map(cls.from_json, cls.collection.find({"admin_permissions.responder": True})))

    async def delete_state_message(self):
        await bot.delete_message(self.id, self.id_of_message_promoter_to_type)
