import toml
import sys

from distutils.errors import DistutilsSetupError


def validate_list_of_str(name, data):
    if name in data:
        if not isinstance(data[name], list):
            raise DistutilsSetupError('"%s" should be a list' % name)
        elif not all([isinstance(i, str) for i in data[name]]):
            raise DistutilsSetupError('"%s" should be a list of strings' % name)

    
def validate_component(toml_string):
    try:
        data = toml.loads(toml_string)
    except Exception as ex:
        raise DistutilsSetupError("component = is not valid toml: %s" % ex)

    allowed_top_level_keys = set(['metadata_version', 'configuration', 'persisted', 'schedule', 'versions'])
    unsupported_keys = set(data.keys()) - allowed_top_level_keys
    if unsupported_keys:
        raise DistutilsSetupError('Unsupported settings for "component =": %s' % (', '.join(unsupported_keys)))

    if 'configuration' in data:
        if not isinstance(data['configuration'], str):
            raise DistutilsSetupError('"configuration" should be a str')
            
    validate_list_of_str('persisted', data)
    validate_list_of_str('schedule', data)
            
    if 'versions' in data:
        if not isinstance(data['versions'], dict):
            raise DistutilsSetupError('"versions" should be a dict')
        for version in data['versions']:
            validate_list_of_str('migrations', version)
            validate_list_of_str('install_requires', version)

            
def setup_keyword(dist, attr, value):
    validate_component(value)

def dist_info(cmd, basename, filename):
    if cmd.distribution.component is not None:
        validate_component(cmd.distribution.component)
        cmd.write_or_delete_file('component', filename, cmd.distribution.component)


def egg_info(cmd, basename, filename):
    dist_info(cmd, basename, filename)


