from pprint import pprint
from typing import List
import requests_to_bd
from classes.json_serializable_class import JsonSerializableClass
from classes.brand import Brand


class Count(JsonSerializableClass):
    def __init__(self, count: int, warehouse_name: str):
        self.count = count
        self.warehouse_name = warehouse_name

    def __repr__(self):
        return f'{self.warehouse_name}: {self.count} шт.'

    def __str__(self):
        return f"{self.warehouse_name}: {self.count} шт."


class SparePart(JsonSerializableClass):
    def __init__(self, brand: Brand, name: str, code: str, counts: List[Count],
                 photos: List[str]):
        self.counts = counts
        self.brand = brand
        self.name = name
        self.photos = photos
        self.code = code

    @classmethod
    def search(cls, query: str):
        from classes.search_result import SearchResult
        results_dicts = requests_to_bd.get_parts_by_text(query)["items"]
        code_sp = cls.get_by_code(query)
        if code_sp:
            results_dicts.append({"code": code_sp.code,
                                  "name": code_sp.name,
                                  "brandid": code_sp.brand.uid})
        return SearchResult(results_dicts)

    @classmethod
    def get_by_code(cls, code: str, brand_uid: str = None):
        """
        :rtype :SparePart
        """
        if brand_uid is not None and Brand.get_by_uid(brand_uid) is None:
            return None
        result_dict = requests_to_bd.get_part_by_code(code, brand_uid)
        if result_dict['result'] in ['Товар или ячейка не найдены', 'Товар не найден']:
            return None
        result_dict = result_dict["item"]
        return cls(Brand.get_by_uid(result_dict["brandid"]),
                   result_dict["name"],
                   result_dict["code"],
                   [Count(counts_dict["count"], counts_dict["namewh"]) for counts_dict in result_dict["counts"]],
                   result_dict["imgs"])

    def __repr__(self):
        return f'{self.name=} {self.code=} {self.brand=} {self.counts=} {self.photos=} '


class SparePartStripped(JsonSerializableClass):
    def __init__(self, brand: Brand, name: str, code: str,):
        self.brand = brand
        self.name = name
        self.code = code

    def get_full_info(self) -> SparePart:
        return SparePart.get_by_code(self.code, self.brand.uid)

    def __repr__(self):
        return f'{self.name=} {self.code=} {self.brand=} '

    @classmethod
    def from_JSON(cls, sp_dict: dict):
        return cls(Brand.from_JSON(sp_dict["brand"]), sp_dict["name"], sp_dict["code"])


if __name__ == '__main__':
    from classes.search_result import SearchResult
    res = SparePart.search('Болт')
    # res = SparePart.search('402184A1')
    sr = SearchResult.from_JSON(res.to_JSON())
    print(sr)
