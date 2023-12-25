import os
from base64 import b64decode
import requests_to_bd
from .json_serializable_class import JsonSerializableClass


class Photo(JsonSerializableClass):
    def __init__(self, photo_id: str):
        self.id = photo_id

    def download(self):
        data = requests_to_bd.get_image_by_id(self.id)["data"]
        with open(f'{self.id}.jpg', 'wb') as file:
            file.write(b64decode(data))
        return f'{self.id}.jpg'

    def remove(self):
        os.remove(f'{self.id}.jpg')
