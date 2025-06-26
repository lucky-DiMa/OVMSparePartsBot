import os
from dotenv import dotenv_values
from pkg_resources import set_extraction_path

# Get the absolute path to the directory containing this config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build absolute paths to your .env files
SECRET_ENV_PATH = os.path.join(BASE_DIR, ".env.secret")
SHARED_ENV_PATH = os.path.join(BASE_DIR, ".env.shared")


secret_config_dict = dict(dotenv_values(SECRET_ENV_PATH))
shared_config_dict = dict(dotenv_values(SHARED_ENV_PATH))
TEST = bool(int(shared_config_dict["TEST"]))  # 0 = False, any other eq True
TOKEN = secret_config_dict[("TEST_" if TEST else "") + "TOKEN"]
BASE_WEBHOOK_URL = secret_config_dict["BASE_WEBHOOK_URL"]
MONGO_AUTH_LINK = secret_config_dict["MONGO_AUTH_LINK"]
RDP_1C_URL = secret_config_dict["RDP_1C_URL"]
ACCESS_KEY = secret_config_dict["ACCESS_KEY"]
BY_WEBHOOK = bool(int(shared_config_dict["BY_WEBHOOK"]))  # 0 = False, any other eq True
MONGO_CLUSTER_NAME = shared_config_dict[("TEST_" if TEST else "") + "MONGO_CLUSTER_NAME"]
REDIS_URL = shared_config_dict["REDIS_URL"]
MANUAL_URL = shared_config_dict["MANUAL_URL"]

text_of_contacts_message = 'Режим работы: Пн-пт: 08:00 - 17:00, сб-вс: выходной\nНаши контакты:\nОрлов Антон Викторович: +79827611859\nEmail: oav@ovm.group'
