import json
from _clutter import *

try:
    from ClutterBindings import *

    def core():
        return ClutterCore.instance()
except ImportError:
    pass


def cmdj(command):
    """Execute a JSON command and return the result as a dictionary"""
    return json.loads(cmd(command))


