from aiogram.types import Message
from dotenv import dotenv_values


secret_config_dict = dict(dotenv_values(".env.secret"))
shared_config_dict = dict(dotenv_values(".env.shared"))
TOKEN = secret_config_dict["TOKEN"]
BASE_WEBHOOK_URL = secret_config_dict["BASE_WEBHOOK_URL"]
MONGO_AUTH_LINK = secret_config_dict["MONGO_AUTH_LINK"]
BY_WEBHOOK = bool(int(shared_config_dict["BY_WEBHOOK"]))  # 0 = False, any other eq True
MONGO_CLUSTER_NAME = shared_config_dict["MONGO_CLUSTER_NAME"]
REDIS_URL = shared_config_dict["REDIS_URL"]


def is_command(message: Message):
    for entity in message.entities:
        if entity.type == 'bot_command':
            return entity.get_text(message.text)[1:]
    return None


text_of_contacts_message = 'Режим работы: Пн-пт: 08:00 - 17:00, сб-вс: выходной\nНаши контакты:\nОрлов Антон Викторович: +79827611859\nEmail: oav@ovm.group'
