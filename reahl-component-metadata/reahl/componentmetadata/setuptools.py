import toml
import pathlib


try:
    from setuptools.errors import SetupError, FileError
except ImportError:
    from distutils.errors import DistutilsSetupError as SetupError
    from distutils.errors import DistutilsFileError as FileError

def validate_list_of_str(name, data):
    if name in data:
        if not isinstance(data[name], list):
            raise SetupError('"%s" should be a list' % name)
        elif not all([isinstance(i, str) for i in data[name]]):
            raise SetupError('"%s" should be a list of strings' % name)


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
                raise SetupError('Exception when trying to load %s: %s' % (cls.pyproject_file(), ex)) from ex
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
            raise SetupError('[%s] Unsupported keys for [tool.reahl-component]: %s' % (self.pyproject_file(), ', '.join(unsupported_keys)))

        if 'configuration' in self.data:
            if not isinstance(self.data['configuration'], str):
                raise SetupError('[%s] "configuration" should be a str' % self.pyproject_file())

        validate_list_of_str('persisted', self.data)
        validate_list_of_str('schedule', self.data)

        if 'versions' in self.data:
            if not isinstance(self.data['versions'], dict):
                raise SetupError('"versions" should be a dict')
            for version_number, version in self.data['versions'].items():
                validate_list_of_str('migrations', version)
                validate_list_of_str('dependencies', version)
                if 'install_requires' in version:
                    raise SetupError('[%s] "install_requires" not allowed in [tool.reahl-component.versions."%s"]. Did you mean "dependencies"?' % (self.pyproject_file(), version_number))
                    
                unsupported_version_keys = set(version.keys()) - {'migrations', 'dependencies'}
                if unsupported_version_keys:
                    raise SetupError('[%s] Unsupported keys for [tool.reahl-component.versions."%s"]: %s' % (self.pyproject_file(), version_number, (', '.join(unsupported_version_keys))))


def dist_info(cmd, basename, filename):
    component_metadata = ComponentMetadata.from_pyproject()
    if component_metadata.exists:
        component_metadata.validate()
        cmd.write_file('component', filename, component_metadata.as_toml_string())
    else:
        cmd.write_or_delete_file('component', filename, '')

