from __future__ import annotations
from enum import Enum
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from classes.classproperty import classproperty


class AdminPermissions(Enum):
    invite_new_users = 'Приглашать новых сотрудников'
    responder = 'Команда /requests, возможность управлять запросами на доступ'
    choose_admins = 'Выбирать администраторов'
    permissions_list: list[AdminPermissions]
    permissions_dict: dict[str, AdminPermissions]

    @classproperty
    def permissions_list(cls):
        return list(cls.__members__.values())

    @classproperty
    def permissions_dict(cls):
        return cls._member_map_


class AdminPermissionsDict(dict[str | AdminPermissions, bool]):
    def __getitem__(self, item: AdminPermissions):
        if isinstance(item, str):
            return super().__getitem__(item)
        return super().__getitem__(item.name)

    def __setitem__(self, key: str | AdminPermissions, value: bool):
        if isinstance(key, str):
            raise Exception("Can't set value by string key")
        super().__setitem__(key.name, value)



    @classmethod
    def _validate(cls, data: dict[str, bool]) -> AdminPermissionsDict:
        result = cls()
        for key, value in data.items():
            if key not in AdminPermissions.__members__:
                raise ValueError(f"Invalid permission key: {key}")
            result[AdminPermissions.permissions_dict[key]] = value
        return result

    @classmethod
    def _serialize(cls, value: AdminPermissionsDict) -> dict[str, bool]:
        return dict(value)