from typing import List
import requests_to_bd
from classes.brand import Brand


class Count:
    def __init__(self, count: int, warehouse_name: str):
        self.count = count
        self.warehouse_name = warehouse_name

    def __repr__(self):
        return f'{self.warehouse_name}: {self.count} шт.'

    def __str__(self):
        return f"{self.warehouse_name}: {self.count} шт."


class SparePart:
    def __init__(self, brand: Brand, naming: str, article: str, counts: List[Count],
                 photos: List[str]):
        self.counts = counts
        self.brand = brand
        self.naming = naming
        self.photos = photos
        self.article = article

    @classmethod
    def search(cls, query: str, brand_uid: str = None):
        from classes.search_result import NoBrandSearchResult, BrandSearchResult
        if brand_uid is not None and Brand.get_by_uid(brand_uid) is None:
            return None
        results_dicts = requests_to_bd.get_parts_by_text(query, brand_uid)["items"]
        article_sp = cls.get_by_article(query, brand_uid)
        if article_sp:
            results_dicts.append({"code": article_sp.article,
                                  "name": article_sp.naming,
                                  "brandid": article_sp.brand.uid})
        if not brand_uid:
            return NoBrandSearchResult(results_dicts)
        return BrandSearchResult(query, results_dicts, brand_uid)

    @classmethod
    def get_by_article(cls, article: str, brand_uid: str = None):
        """
        :rtype :SparePart
        """
        if brand_uid is not None and Brand.get_by_uid(brand_uid) is None:
            return None
        result_dict = requests_to_bd.get_part_by_article(article, brand_uid)
        if result_dict['result'] in ['Товар или ячейка не найдены', 'Товар не найден']:
            return None
        result_dict = result_dict["item"]
        return cls(Brand.get_by_uid(result_dict["brandid"]),
                   result_dict["name"],
                   result_dict["code"],
                   [Count(counts_dict["count"], counts_dict["namewh"]) for counts_dict in result_dict["counts"]],
                   result_dict["imgs"])

    def __repr__(self):
        return f'{self.naming} {self.article} {self.brand} {self.counts} {self.photos} '


if __name__ == '__main__':
    print(SparePart.get_by_article(input('A: '), input('B: ')))
