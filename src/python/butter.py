import json
from _butter import *

try:
    from ButterBindings import *

    def core():
        return ButterCore.instance()
except ImportError:
    pass


def cmdj(command):
    """Execute a JSON command and return the result as a dictionary"""
    return json.loads(cmd(command))


