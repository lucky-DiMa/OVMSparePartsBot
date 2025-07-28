from __future__ import annotations
from enum import Enum

from classes.classproperty import classproperty


class AdminPermissions(Enum):
    invite_new_users = 'Приглашать новых сотрудников'
    responder = 'Команда /requests, возможность управлять запросами на доступ'
    choose_admins = 'Выбирать администраторов'
    permissions_list: list[AdminPermissions]

    @classproperty
    def permissions_list(self):
        return list(AdminPermissions.__members__.values())


class AdminPermissionsDict(dict[str | AdminPermissions, bool]):
    def __getitem__(self, item: AdminPermissions):
        if isinstance(item, str):
            return super().__getitem__(item)
        return super().__getitem__(item.name)

    def __setitem__(self, key: str | AdminPermissions, value: bool):
        if isinstance(key, str):
            raise Exception("Can't set value by string key")
        super().__setitem__(key.name, value)
