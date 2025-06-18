from __future__ import annotations
import os
from base64 import b64decode
from utils import RequestsTo1cService
from classes.json_serializable_object import JsonSerializableObject


class Photo(JsonSerializableObject):
    fields = {'id': str}
    def __init__(self, photo_id: str):
        self.id = photo_id

    async def download(self):
        data = (await RequestsTo1cService.get_image_by_id(self.id))["data"]
        with open(f'{self.id}.jpg', 'wb') as file:
            file.write(b64decode(data))
        return f'{self.id}.jpg'

    def remove(self):
        os.remove(f'{self.id}.jpg')
