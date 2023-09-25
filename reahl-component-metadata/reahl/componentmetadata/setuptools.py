import toml
import sys
import pathlib

from distutils.errors import DistutilsSetupError, DistutilsFileError


def validate_list_of_str(name, data):
    if name in data:
        if not isinstance(data[name], list):
            raise DistutilsSetupError('"%s" should be a list' % name)
        elif not all([isinstance(i, str) for i in data[name]]):
            raise DistutilsSetupError('"%s" should be a list of strings' % name)


class ComponentMetadata:
    @classmethod
    def pyproject_file(cls):
        return pathlib.Path('pyproject.toml').absolute()
    
    @classmethod
    def from_pyproject(cls):
        data = {}
        if cls.pyproject_file().exists():
            try:
                data = toml.load(cls.pyproject_file()).get('tool', {}).get('reahl-component', {})
            except Exception as ex:
                raise DistutilsSetupError('Exception when trying to load %s: %s' % (cls.pyproject_file(), ex)) from ex
        return cls(data)
    
    def __init__(self, data):
        self.data = data
        self.data['metadata_version'] = '1.1.0'

    @property
    def exists(self):
        return bool(self.data)
        
    def as_toml_string(self):
        return toml.dumps(self.data)

    def validate(self):
        allowed_top_level_keys = set(['metadata_version', 'configuration', 'persisted', 'schedule', 'versions'])
        unsupported_keys = set(self.data.keys()) - allowed_top_level_keys
        if unsupported_keys:
            raise DistutilsSetupError('[%s] Unsupported keys for [tool.reahl-component]: %s' % (self.pyproject_file(), ', '.join(unsupported_keys)))

        if 'configuration' in self.data:
            if not isinstance(self.data['configuration'], str):
                raise DistutilsSetupError('[%s] "configuration" should be a str' % self.pyproject_file())

        validate_list_of_str('persisted', self.data)
        validate_list_of_str('schedule', self.data)

        if 'versions' in self.data:
            if not isinstance(self.data['versions'], dict):
                raise DistutilsSetupError('"versions" should be a dict')
            for version_number, version in self.data['versions'].items():
                validate_list_of_str('migrations', version)
                validate_list_of_str('dependencies', version)
                if 'install_requires' in version:
                    raise DistutilsSetupError('[%s] "install_requires" not allowed in [tool.reahl-component.versions."%s"]. Did you mean "dependencies"?' % (self.pyproject_file(), version_number))
                    
                unsupported_version_keys = set(version.keys()) - {'migrations', 'dependencies'}
                if unsupported_version_keys:
                    raise DistutilsSetupError('[%s] Unsupported keys for [tool.reahl-component.versions."%s"]: %s' % (self.pyproject_file(), version_number, (', '.join(unsupported_version_keys))))
                    

                
def setup_keyword(dist, attr, value):
    ComponentMetadata.from_string(value).validate()

def dist_info(cmd, basename, filename):
    if cmd.distribution.component is not None:
        raise DistutilsFileError('Old metadata found. This version of reahl-component-metadata expects all your metadata to be in a PEP 621 pyproject.toml file')
    component_metadata = ComponentMetadata.from_pyproject()
    if component_metadata.exists:
        component_metadata.validate()
        cmd.write_file('component', filename, component_metadata.as_toml_string())
    else:
        cmd.write_or_delete_file('component', filename, '')


def egg_info(cmd, basename, filename):
    dist_info(cmd, basename, filename)


