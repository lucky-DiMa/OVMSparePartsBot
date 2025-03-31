from typing import Any, ClassVar
from classes.classproperty import classproperty


class JsonSerializableObject:
    fields: ClassVar[dict[str, type]]

    @classproperty
    @classmethod
    def fields_keys(cls) -> list[str]:
        return list(cls.fields.keys())

    @staticmethod
    def obj_to_JSON(obj: Any) -> dict[str, Any] | list[Any]:
        if type(obj) == list:
            return JsonSerializableObject.list_to_JSON(obj)
        if hasattr(obj, 'to_JSON'):
            return obj.to_JSON()
        return obj

    @staticmethod
    def list_to_JSON(list_: list) -> list:
        res = []
        for obj in list_:
            res.append(JsonSerializableObject.obj_to_JSON(obj))
        return res

    def to_JSON(self) -> dict[str, Any]:
        return {field: self.obj_to_JSON(self.__getattribute__(field)) for field in self.__class__.fields.keys()}

    @staticmethod
    def list_from_JSON[list_T: list](list_type: type[list_T], json_list: list[Any]) -> list_T:
        t = list_type.__args__[0]
        res: list_type = []
        for obj in json_list:
            res.append(JsonSerializableObject.obj_from_JSON(t, obj))
        return res

    @staticmethod
    def obj_from_JSON[T: type](cls: type[T], json_obj: dict[str, Any] | list[Any]) -> T:
        if hasattr(cls, '__origin__') and cls.__origin__ == list:
            return JsonSerializableObject.list_from_JSON(cls, json_obj)
        if hasattr(cls, 'from_JSON'):
            return cls.from_JSON(json_obj)
        return json_obj

    @classmethod
    def from_JSON[T](cls: type[T], json_dict: dict) -> T:
        return cls(*[JsonSerializableObject.obj_from_JSON(field_type, json_dict[field]) for field, field_type in cls.fields.items()])
