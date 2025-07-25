from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Any, List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from classes import User
from classes.states import States
from classes.mongo_db_object import MongoDBObject
from classes.user import PermissionDeniedException
from bot.create_bot import bot
from utils import get_next_id, now_time, beauty_datetime


class AccessRequestStatuses(Enum):
    waiting = 'ожидание'
    canceled = 'отменён'
    accepted = 'принят'
    rejected = 'отклонён'
    rejected_and_banned = 'отклонён и заблокирован'


class ModifyException(Exception):
    """You cannot modify this request now"""


class ResponseException(Exception):
    """You cannot respond this request now"""


class RequestNotFoundException(Exception):
    """Request with given ID not found"""


class CancelException(Exception):
    """You cannot cancel this request now"""


class AccessRequest(MongoDBObject):
    collection_name = 'AccessRequests'
    fields = {'id': int,
              'user_id': int,
              'user_phone': str,
              'status': str,
              'creation_datetime': datetime,
              'last_modify_datetime': datetime,
              'responder_id': int}

    def __init__(self, _id: int, user_id: int,
                 user_phone: str,
                 status: str,
                 creation_datetime: datetime,
                 last_modify_datetime: datetime = None,
                 response_datetime: datetime = None,
                 responder_id: int = None):
        self.__id = _id
        self.__user_id = user_id
        self.__user_phone = user_phone
        self.__status = status
        self.__creation_datetime = creation_datetime
        self.__last_modify_datetime = last_modify_datetime
        self.__response_datetime = response_datetime
        self.__responder_id = responder_id

    @staticmethod
    def editing_keyboard():
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Отозвать запрос', callback_data='CANCEL REG')]])
    @property
    def responding_keyboard(self):
        if self.able_to_response_to:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Принять', callback_data=f'ACCEPT REG {self.id}'),
                 InlineKeyboardButton(text='Отклонить', callback_data=f'REJECT REG {self.id}')],
                [InlineKeyboardButton(text=f'Заблокировать {self.user_phone}',
                                      callback_data=f'REJECT AND BAN REG {self.id}')],
                [InlineKeyboardButton(text='↻ Обновить',
                                      callback_data=f'VIEW REQUEST {self.id}')],
                [InlineKeyboardButton(text="<< Назад >>", callback_data='UPDATE REQUESTS')]])
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="<< Назад >>", callback_data='UPDATE REQUESTS')]])

    @classmethod
    def set_field_by_id(cls, _id: int, field: str, value: Any):
        cls.collection.update_one({'_id': _id}, {'$set': {field: value}})

    def set_field(self, field: str, value: Any):
        self.__class__.set_field_by_id(self.__id, field, value)

    @property
    def id(self):
        return self.__id

    @property
    def user_id(self):
        return self.__user_id

    @property
    def user_phone(self):
        return self.__user_phone

    @property
    def status(self):
        return self.__status

    @property
    def creation_datetime(self):
        return self.__creation_datetime

    @property
    def last_modify_datetime(self):
        return self.__last_modify_datetime

    @property
    def response_datetime(self):
        return self.__response_datetime

    @property
    def responder_id(self):
        return self.__responder_id

    def update_last_modify_datetime(self):
        if not self.able_to_modify:
            raise ModifyException()
        self.set_field('last_modify_datetime', now_time())

    def accept(self, responder_id: int):
        if not self.able_to_response_to:
            raise ResponseException()
        responder = User.get_by_id(responder_id)
        if not responder.is_owner:
            if not responder.is_admin:
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: choose_admins. Reason: user is not admin.')
            if not responder.is_allowed('responder'):
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: responder. Reason: user is admin but has not this permission')
        self.__status = AccessRequestStatuses.accepted.name
        self.set_field('status', self.__status)
        now_time_ = now_time()
        self.__response_datetime = now_time_
        self.set_field('response_datetime', now_time_)
        self.__responder_id = responder.id
        self.set_field('responder_id', responder_id)
        User.get_by_id(self.__user_id).set_state(States.NONE)

    def reject(self, responder_id: int):
        if not self.able_to_response_to:
            raise ResponseException()
        responder = User.get_by_id(responder_id)
        if not responder.is_owner:
            if not responder.is_admin:
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: choose_admins. Reason: user is not admin.')
            if not responder.is_allowed('responder'):
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: responder. Reason: user is admin but has not this permission')
        self.__status = AccessRequestStatuses.rejected.name
        self.set_field('status', self.__status)
        now_time_ = now_time()
        self.__response_datetime = now_time_
        self.set_field('response_datetime', now_time_)
        self.__responder_id = responder.id
        self.set_field('responder_id', responder_id)
        User.delete_by_id(self.__user_id)

    #TODO
    def reject_and_ban(self, responder_id: int):
        if not self.able_to_response_to:
            raise ResponseException()
        responder = User.get_by_id(responder_id)
        if not responder.is_owner:
            if not responder.is_admin:
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: choose_admins. Reason: user is not admin.')
            if not responder.is_allowed('responder'):
                raise PermissionDeniedException(
                    f'User: "{responder.phone}" {responder.id}. Permission: responder. Reason: user is admin but has not this permission')
        self.__status = AccessRequestStatuses.rejected_and_banned.name
        self.set_field('status', self.__status)
        now_time_ = now_time()
        self.__response_datetime = now_time_
        self.set_field('response_datetime', now_time_)
        self.__responder_id = responder.id
        self.set_field('responder_id', responder_id)
        User.ban_by_id(self.__user_id)

    def cancel(self):
        if not self.able_to_response_to:
            raise CancelException()
        self.__status = AccessRequestStatuses.canceled.name
        self.set_field('status', self.__status)
        now_time_ = now_time()
        self.__response_datetime = now_time_
        self.set_field('response_datetime', now_time_)
        User.delete_by_id(self.__user_id)

    @classmethod
    def get_by_id(cls, _id: int) -> AccessRequest:
        data = cls.collection.find_one({'id': _id})
        if not data:
            raise RequestNotFoundException(f"Given ID: {_id}")
        return cls.from_json(data)

    @classmethod
    def get_all(cls) -> List[AccessRequest] | list:
        return list(map(cls.from_json, cls.collection.find()))

    @classmethod
    def get_waiting(cls) -> List[AccessRequest] | list:
        return list(map(cls.from_json, cls.collection.find({"status": AccessRequestStatuses.waiting.name})))

    @classmethod
    def get_waiting_by_user_id(cls, user_id: int) -> AccessRequest | None:
        return cls.from_json(
            cls.collection.find_one({"user_id": user_id, "status": AccessRequestStatuses.waiting.name}))

    # @classmethod
    # def get_latest_by_user_id(cls, user_id: int) -> AccessRequest | None:
    #     ODO find latest request by user_id
    #     ...

    @classmethod
    def next_id(cls) -> int:
        return get_next_id(cls.collection.name)

    @classmethod
    def create(cls, user: User) -> AccessRequest:
        request = AccessRequest(cls.next_id(), user.id, user.phone,
                                AccessRequestStatuses.waiting.name, now_time())
        cls.collection.insert_one(request.to_json())
        return request

    @property
    def able_to_response_to(self) -> bool:
        return self.status == AccessRequestStatuses.waiting.name

    @property
    def able_to_modify(self) -> bool:
        return self.status == AccessRequestStatuses.waiting.name

    async def get_info(self, for_sender: bool):
        resp = (
                   "Запрос на получение доступа к боту был отправлен!\n\n" if for_sender else "") + f'Запрос <u><i>#{self.id}</i></u>:\nНомер телефона: <code>{self.user_phone}</code>\nИнформация об аккаунте в Telegram:\nID: <code>{self.user_id}</code>\nПолное имя: <code>{(await bot.get_chat(self.__user_id)).full_name}</code>\nUsername: {"@" + (await bot.get_chat(self.__user_id)).username if (await bot.get_chat(self.__user_id)).username else "<code>не указан</code>"}\n\nВремя создания запроса: <code>{beauty_datetime(self.__creation_datetime, 1)}</code>\nВремя последнего изменения: <code>{beauty_datetime(self.__last_modify_datetime, 1) if self.__last_modify_datetime else "запрос не был изменён"}</code>\n\nСтатус: <code>{AccessRequestStatuses.__getitem__(self.status).value}</code>'
        if not self.able_to_response_to:
            if self.status == AccessRequestStatuses.canceled.name:
                resp += '\nВремя отмены: <code>' + beauty_datetime(self.__response_datetime, 1) + '</code>'
            else:
                resp += '\nВремя ответа: <code>' + beauty_datetime(self.__response_datetime, 1) + '</code>'
                resp += f'\n\nАдминистратор, ответивший на запрос:\nID: <code>{self.__responder_id}</code>'
        return resp
