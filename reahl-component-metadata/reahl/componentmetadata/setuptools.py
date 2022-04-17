import toml
import sys

from distutils.errors import DistutilsSetupError

def setup_keyword(dist, attr, value):
    raise DistutilsSetupError("boo")
    data = toml.loads(value)
    if False: 
        raise DistutilsSetupError("'component' should be valid toml")


def dist_info(cmd, basename, filename):
    if cmd.distribution.component is not None:
        try:
            data = toml.loads(cmd.distribution.component)
        except Exception as ex:
            raise DistutilsSetupError("component = is not valid toml: %s" % ex)
            
        cmd.write_or_delete_file('component', filename, cmd.distribution.component)


def egg_info(cmd, basename, filename):
    dist_info(cmd, basename, filename)


# TODO: validate
# - if you have component= you must have a dependency on reahl-component
