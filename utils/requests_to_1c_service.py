from pprint import pprint
from typing import Any

from aiohttp import ClientSession

from config import RDP_1C_URL


async def post_to_1c(**kwargs) -> dict[str, Any]:
    json = {"warehouse": "ОМ Партс Ирбит*",
            "app": "WH-mobile",
            "useruid": "64b432f6-705a-11ec-9171-001b21e4770b",
            "organization": "ООО \"ОМ партс\"",
            **kwargs}
    resp = None
    async with ClientSession() as session:
        async with await session.post(RDP_1C_URL, json=json) as response:
            resp = await response.json(content_type=response.content_type)
    return resp


class RequestsTo1cService:
    @staticmethod
    async def get_parts_by_text(text: str, brand_id: str | None = None) -> dict[str, Any]:
        json = {"text": text,
                "uid": brand_id,
                "operation": "searchitem2"}
        if brand_id is None:
            json.pop("uid")
        return await post_to_1c(**json)

    @staticmethod
    async def get_part_by_code(code: str | int, brand_id: str | None = None) -> dict[str, Any]:
        json = {"shk": code,
                "uid": brand_id,
                "operation": "scan2"}
        if brand_id is None:
            json.pop("uid")
        return await post_to_1c(**json)

    @staticmethod
    async def get_image_by_id(img_id: str | int) -> dict[str, Any]:
        json = {"operation": "getimg",
                "imgpath": img_id}

        return await post_to_1c(**json)

    @staticmethod
    async def get_analogs_by_code(code: str) -> dict[str, Any]:
        json = {"operation":"scan3",
                "shk": code,}
        return await post_to_1c(**json)

    @staticmethod
    async def get_brands() -> dict[str, Any]:
        json = {"operation": "getbrands"}
        return await post_to_1c(**json)


if __name__ == '__main__':
    import asyncio
    # pprint(get_brands())
    pprint(asyncio.run(RequestsTo1cService.get_parts_by_text(input('TEXT: '))))
    # pprint(get_analogs_by_code(input('CODE: '))['item']['analogs'])
    # pprint(get_brands())
    # pprint(asyncio.run(RequestsTo1cService.get_part_by_code(input('code: '))))
