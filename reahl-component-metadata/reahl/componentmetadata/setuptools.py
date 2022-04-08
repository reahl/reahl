import json
import sys

from distutils.errors import DistutilsSetupError

def setup_keyword(dist, attr, value):
    json.loads(cmd.distribution.component)
    if False: #not isinstance(value, dict):
        raise DistutilsSetupError("'component' should be a dict")


def egg_info(cmd, basename, filename):
    if cmd.distribution.component:
        cmd.write_or_delete_file('component', filename, cmd.distribution.component)
