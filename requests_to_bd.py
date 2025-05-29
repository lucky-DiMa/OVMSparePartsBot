import base64
from json import loads
from pprint import pprint

import requests


def get_parts_by_text(text: str, brand_id: str | None = None):
    """
    :rtype :dict
    """
    json = {"warehouse": "ОМ Партс Ирбит*",
            "text": text,
            "app": "WH-mobile",
            "useruid": "64b432f6-705a-11ec-9171-001b21e4770b",
            "uid": brand_id,
            "operation": "searchitem2",
            "organization": "ООО \"ОМ партс\""}
    if brand_id is None:
        json.pop("uid")
    response = requests.post('http://rdp.ovm.group:33900', json=json)
    return loads(response.text)


def get_part_by_code(code: str | int, brand_id: str | None = None):
    """
    :rtype :dict
    """
    json = {"operation": "scan2",
            "shk": code,
            "app": "WH-mobile",
            "organization": "ООО \"ОМ партс\"",
            "useruid": "64b432f6-705a-11ec-9171-001b21e4770b",
            "uid": brand_id,
            "warehouse": "ОМ Партс Ирбит*"}
    if brand_id is None:
        json.pop("uid")
    response = requests.post('http://rdp.ovm.group:33900', json=json)
    return loads(response.text)


def get_image_by_id(img_id: str | int):
    """
    :rtype :dict
    """
    response = requests.post('http://rdp.ovm.group:33900', json={"organization": "ООО \"ОМ партс\"",
                                                                 "app": "WH-mobile",
                                                                 "operation": "getimg",
                                                                 "useruid": "64b432f6-705a-11ec-9171-001b21e4770b",
                                                                 "warehouse": "ОМ Партс Ирбит*",
                                                                 "imgpath": img_id})
    return loads(response.text)


def get_analogs_by_code(code: str):
    """
    :rtype :dict
    """
    response = requests.post('http://rdp.ovm.group:33900', json={"operation":"scan3",
                                                                 "shk": code,
                                                                 "app":"WH-mobile",
                                                                 "organization":"ООО \"ОМ партс\"",
                                                                 "useruid":"64b432f6-705a-11ec-9171-001b21e4770b"})
    return loads(response.text)


def get_brands():
    response = requests.post('http://rdp.ovm.group:33900', json={"operation": "getbrands",
                                                                 "organization": "ООО \"ОМ партс\"",
                                                                 "app": "WH-mobile"})
    return loads(response.text)


if __name__ == '__main__':
    # pprint(get_brands())
    pprint(get_parts_by_text(input('TEXT: ')))
    # pprint(get_analogs_by_code(input('CODE: '))['item']['analogs'])
    # pprint(get_brands())
    # pprint(get_part_by_code(input('code: ')))
