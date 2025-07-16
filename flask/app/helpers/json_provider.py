from flask.json.provider import DefaultJSONProvider
from datetime import time, date, datetime
import json


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime('%H:%M')
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
