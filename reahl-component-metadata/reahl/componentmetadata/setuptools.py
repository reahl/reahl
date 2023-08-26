import toml
import sys
import pathlib

from distutils.errors import DistutilsSetupError


def validate_list_of_str(name, data):
    if name in data:
        if not isinstance(data[name], list):
            raise DistutilsSetupError('"%s" should be a list' % name)
        elif not all([isinstance(i, str) for i in data[name]]):
            raise DistutilsSetupError('"%s" should be a list of strings' % name)


class ComponentMetadata:
    @classmethod
    def from_pyproject(cls):
        pyproject_file = pathlib.Path('pyproject.toml')
        data = {}
        if pyproject_file.exists():
            try:
                data = toml.load(pyproject_file).get('tool', {}).get('reahl-component', {})
            except Exception as ex:
                raise DistutilsSetupError("component = is not valid toml: %s" % ex)
        return cls(data)
    
    @classmethod
    def from_string(cls, toml_string):
        try:
            data = toml.loads(toml_string)
        except Exception as ex:
            raise DistutilsSetupError("component = is not valid toml: %s" % ex)
        return cls(data)

    def __init__(self, data):
        self.data = data
        self.data['metadata_version'] = '1.0.0'

    @property
    def exists(self):
        return bool(self.data)
        
    def as_toml_string(self):
        return toml.dumps(self.data)
    
    def validate(self):
        allowed_top_level_keys = set(['metadata_version', 'configuration', 'persisted', 'schedule', 'versions'])
        unsupported_keys = set(self.data.keys()) - allowed_top_level_keys
        if unsupported_keys:
            raise DistutilsSetupError('Unsupported settings for "component =": %s' % (', '.join(unsupported_keys)))

        if 'configuration' in self.data:
            if not isinstance(self.data['configuration'], str):
                raise DistutilsSetupError('"configuration" should be a str')

        validate_list_of_str('persisted', self.data)
        validate_list_of_str('schedule', self.data)

        if 'versions' in self.data:
            if not isinstance(self.data['versions'], dict):
                raise DistutilsSetupError('"versions" should be a dict')
            for version in self.data['versions']:
                validate_list_of_str('migrations', version)
                validate_list_of_str('install_requires', version)

                
def setup_keyword(dist, attr, value):
    ComponentMetadata.from_string(value).validate()

def dist_info(cmd, basename, filename):
    if cmd.distribution.component is not None:
        component_metadata = ComponentMetadata.from_string(cmd.distribution.component)
    else:
        component_metadata = ComponentMetadata.from_pyproject()
    if component_metadata.exists:
        component_metadata.validate()
        cmd.write_file('component', filename, component_metadata.as_toml_string())
    else:
        cmd.write_or_delete_file('component', filename, '')


def egg_info(cmd, basename, filename):
    dist_info(cmd, basename, filename)


