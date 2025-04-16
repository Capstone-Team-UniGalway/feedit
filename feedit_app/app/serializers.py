import json
from enum import Enum
from django.contrib.sessions.serializers import JSONSerializer
from django.utils.functional import Promise


class SafeEnumEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle enums
        if isinstance(obj, Enum):
            return str(obj)

        # Handle Django lazy translations (e.g. __proxy__)
        if isinstance(obj, Promise):
            return str(obj)  # Forces evaluation to actual string

        return super().default(obj)


class SafeEnumJSONSerializer(JSONSerializer):
    def dumps(self, obj):
        return json.dumps(obj, cls=SafeEnumEncoder).encode("latin-1")

    def loads(self, data):
        return json.loads(data.decode("latin-1"))
