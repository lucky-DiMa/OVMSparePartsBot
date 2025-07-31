from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import NamedTuple, Any, Callable, Concatenate, ClassVar

from aiogram import types
from pydantic import Field
from typing_extensions import ParamSpec

from classes.admin_permissions import AdminPermissions, AdminPermissionsDict
from classes.states import State, States
from classes.mongo_db_object import MongoDBModel
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

def check_permission(permission_name: str):
    def decorator[P: ParamSpec, R](func: Callable[[User, P], R]) -> Callable[[User, P], R]:
        @functools.wraps(func)
        def wrapper(self: User, *args: Any, **kwargs: Any):
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
                    raise PermissionDeniedException(
                        f'User: {self.id}. Permission: choose_admins. Reason: user is admin and have this permission but he is not owner and can not allow someone to choose admins.')
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

class User(MongoDBModel):
    _collection_name = 'Users'
    
    _full_admin_permissions: ClassVar[dict[str, bool]] = AdminPermissionsDict({permission.name: True for permission in AdminPermissions.permissions_list})
    _default_admin_permissions: ClassVar[dict[str, bool]] = AdminPermissionsDict({permission.name: False for permission in AdminPermissions.permissions_list})

    id: int
    phone: str = Field(default="")
    state: str = Field(default=States.JUST_STARTED.name)
    is_admin: bool = Field(default=False)
    admin_permissions: AdminPermissionsDict = Field(default={})
    is_owner: bool = Field(default=False)
    previous_query: str = Field(default="")
    id_of_message_promoter_to_type: int | None = Field(default=None)
    text_of_message_promoter_to_type: str | None = Field(default=None)

    def __get_mongo_object_filter__(self):
        return {'id': self.id}

    @property
    def end_type_text(self) -> str:
        return "NONE" if self.state == 'NONE' else 'Сначала отправьте поисковой запрос!' if self.state == "TYPING QUERY" else "Сначала отправьте сообщение обратной связи!" if self.state == 'TYPING FEEDBACK' else 'Сначала поделитесь своим контактом!'

    def set_state(self, state: States, target: int | str = None):
        self.state = State(state, str(target) if target else None).serialization

    def is_allowed(self, permission_name: str):
        return self.is_owner or (self.is_admin and self.__admin_permissions[permission_name])

    @classmethod
    def reg(cls, tg_id: int) -> User:
        if (user := cls.get_by_id(tg_id)) is None:
            user = User(id=tg_id)
            cls.insert_one(user)
        return user


    @classmethod
    def get_by_id(cls, tg_id: int) -> User | None:
        return cls.get_one_from_mongo({"id": tg_id})

    def delete(self):
        self.__class__.delete_by_id(self.id)

    @classmethod
    def delete_by_id(cls, tg_id: int):
        cls._collection.delete_one({"id": tg_id})
        
    @classmethod
    def delete_all(cls):
        cls._collection.drop()

    @classmethod
    def exists_by_id(cls, tg_id: int):
        return cls._collection.find_one({"id": tg_id}) is not None

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

    @check_permission('choose_admins')
    def allow_permission(self, user_id: int, permission_name: str):
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
        self._collection.update_one({'id': self.id}, {'$set': {field: value}})

    @classmethod
    def __set_field_by_id(cls, _id: int, field: str, value: Any):
        cls._collection.update_one({"id": _id}, {"$set": {field: value}})

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
        return list(map(cls.from_json, cls._collection.find({"admin_permissions.responder": True})))

    async def delete_state_message(self):
        await bot.delete_message(self.id, self.id_of_message_promoter_to_type)


        

if __name__ == "__main__":
    User(id=1358414277).admin_permissions[AdminPermissions.choose_admins] = True
