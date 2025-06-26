from .mongo_connector import mongo_db, get_next_id
from .redis_connector import redis_client, connect_redis, close_redis
from .setup_morphy import morph
from .requests_to_1c_service import RequestsTo1cService
from .time_utils import now_time, beauty_datetime, beauty_date, today
from .check_message_types import is_command