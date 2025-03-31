from pymongo import MongoClient
from config import MONGO_AUTH_LINK, MONGO_CLUSTER_NAME

mongo_db = MongoClient(MONGO_AUTH_LINK)[MONGO_CLUSTER_NAME]