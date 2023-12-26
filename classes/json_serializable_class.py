import json
from datetime import datetime


class JsonSerializableClass:
    def to_JSON(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__ if not isinstance(o, datetime) else str(o),
            sort_keys=True, indent=4))