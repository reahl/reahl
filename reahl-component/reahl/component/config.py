# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Classes in this module manage system configuration.

Each Reahl component can have its own config file. The config files of
all components used by an application are stored in a common
directory. If the config file for a component is missing, defaults are
assumed.

Config files are Python code. Inside a config file, an instance of the
component's Configuration is bound to a variable name.

"""

from __future__ import print_function, unicode_literals, absolute_import, division
import sys
import six
import os.path
import logging
import tempfile
from logging import config
from contextlib import contextmanager

from pkg_resources import require, iter_entry_points, DistributionNotFound

from reahl.component.eggs import ReahlEgg
from reahl.component.context import ExecutionContext


class ConfigurationException(Exception):
    pass

class ExplicitSettingRequired(object):
    pass


class ConfigSetting(object):
    """Used to define one configuration setting on a :class:`Configuration`.
    
    
       :param default: The default value to be used if not specified in a config file.
       :param description: A user readable description explaining what this ConfigSetting is for.
       :param dangerous: Set this to True, if a warning should be emitted when used with the supplied default value.
       :param automatic: Set this to True for a ConfigSetting which is meant to be used for dependency injection.
    """
    _name = None
    def __init__(self, default=ExplicitSettingRequired, description='No description supplied', dangerous=False, automatic=False):
        self.description = description
        self.default = default
        self.dangerous = dangerous
        self.automatic = automatic

    @property
    def defaulted(self):
        return self.default is not ExplicitSettingRequired

    def is_localised(self, obj):
        name = self.name(type(obj))
        for key in dir(obj):
            if key.startswith('%s_' % name):
                return True
        return False
        
    def __get__(self, obj, objtype):
        setting_name = self.name(type(obj))
        if self.is_localised(obj):
            context = ExecutionContext.get_context()
            locale = context.interface_locale if context else ''
            try:
                return obj.__dict__['%s_%s' % (setting_name, locale)]
            except KeyError:
                pass

        if self.is_set(obj):
            return obj.__dict__[setting_name]

        if self.defaulted:
            return self.default

        raise ConfigurationException('%s was not set' % setting_name)

    def __set__(self, obj, value):
        name = self.name(type(obj))
        obj.__dict__[name] = value

    def name(self, objtype):
        if self._name:
            return self._name
        for cls in objtype.mro():
            for name, value in cls.__dict__.items():
                if value is self:
                    self._name = name
                    return name
        raise AttributeError('Could not deduce name for descriptor %s (%s) %s' % (self, self.description, self.default))

    def is_set(self, obj):
        name = self.name(type(obj))
        return name in obj.__dict__

    def is_valid(self, obj):        return self.automatic or self.defaulted or self.is_set(obj)

    def is_dangerous(self, obj):
        return self.dangerous and not self.is_set(obj)


class EntryPointClassList(ConfigSetting):
    """A :class:`ConfigSetting` which is not set by a user at all -- rather, its value (a list of classes
       or other importable Python objects) is read from the entry point named `name`.

       :param name: The name of the entry point to read.
       :param description: (See :class:`ConfigSetting`)
    """
    def __init__(self, name, description='Description not supplied'):
        super(EntryPointClassList, self).__init__(default=[], description=description)
        self.name = name
        
    def __get__(self, instance, owner):
        classes = []
        for i in iter_entry_points(self.name):
            try:
                classes.append(i.load())
            except ImportError as e:
                print('\nWARNING: Cannot import %s, from %s' % (i, i.dist), file=sys.stderr)
                print(e, file=sys.stderr)
            except DistributionNotFound as e:
                print('\nWARNING: Cannot find %s, required by %s' % (e, i.dist), file=sys.stderr)
                
        return classes


class MissingValue(object):
    def __repr__(self):
        return 'MISSING!!'

    
class Configuration(object):
    """A collection of ConfigSettings for a component. To supply configuration for your component,
       subclass from this class and assign each wanted ConfigSetting as a class attribute. Assign
       the required `filename` and `config_key` class attributes in your subclass as well. The resultant
       class should also be listed in the .reahlproject file of your component in a <configuration> element.
    """
    
    filename = None   #: The name of the config file from which this Configuration will be read.
    config_key = None #: The variable name to which an instance of this Configuration will be bound when reading `filename`
    
    def update(self, other):
        for name, value in other.__dict__.items():
            setattr(self, name, value)

    def get_from_string(self, string_key):
        return self.composite_get_attr(string_key.split('.'))

    def composite_get_attr(self, composite_keys):
        config = self
        for key in composite_keys:
            config = getattr(config, key)
        return config

    def get_config_item(self, name):
        return self.__class__.__dict__[name]

    def has_config_item(self, name):
        return isinstance(self.__class__.__dict__.get(name, None), ConfigSetting)
        
    def config_items(self):
        return [(i, self.get_config_item(i))
                for i in dir(self)
                if self.has_config_item(i)]
    
    def validate_contents(self, filename, composite_key, strict_validation):
        unspecifieds = ['%s.%s' % (composite_key, name)
                        for name, config_item in self.config_items()
                        if not config_item.is_valid(self)]
        if unspecifieds:
            raise ConfigurationException('the following configuration parameters were expected in %s, but not found: %s' % \
                                             (filename, ', '.join(unspecifieds)))

        for name, config_item in self.config_items():
            composite_name = '%s.%s' % (composite_key, name)
            if config_item.is_dangerous(self):
                if strict_validation:
                    raise ConfigurationException('%s in %s is using a dangerous default setting: %s' % (composite_name, filename, config_item.default))
                else:
                    logging.getLogger(__name__).warning('%s in %s is using a dangerous default setting: %s' % (composite_name, filename, config_item.default))

    def list_contents(self, filename, composite_key):
        contents = []
        for name, config_item in self.config_items():
            value = MissingValue()
            try:
                value = getattr(self, name)
            except ConfigurationException:
                pass
            composite_name = '%s.%s' % (composite_key, name)
            contents.append( (filename, composite_name, value, config_item) )
        return contents
                                             
    def configure(self, validate=True):
        pass

    def do_injections(self, config):
        pass
        

class NullORMControl(object):
    def do_nothing(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self.do_nothing

    @contextmanager
    def managed_transaction(self):
        yield None


class ReahlSystemConfig(Configuration):
    filename = 'reahl.config.py'
    config_key = 'reahlsystem'
    root_egg = ConfigSetting(description='The root egg of the project', default=os.path.basename(os.getcwd()), dangerous=True)
    connection_uri = ConfigSetting(description='The database connection URI', default='sqlite:///%s' % os.path.join(tempfile.gettempdir(), 'reahl.db'), dangerous=True)
    orm_control = ConfigSetting(default=NullORMControl(), description='The ORM control object to be used', automatic=True)
    debug = ConfigSetting(default=True, description='Enables more verbose logging', dangerous=True)
    databasecontrols = EntryPointClassList('reahl.component.databasecontrols', description='All available DatabaseControl classes')
    translation_packages = EntryPointClassList('reahl.translations', description='All available packages containing translation messages')
    serialise_parallel_requests = ConfigSetting(default=False, description='Whether concurrent requests to the web application should be forcibly serialised')


class ConfigAsDict(dict):
    def __init__(self, config):
        self.config = config
        self['config'] = config

    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self,key)
        if hasattr(self.config, key):
            return getattr(self.config, key)
        raise KeyError(key)

    def update_required(self, key):
        try:
            new_value = dict.__getitem__(self,key)
            setattr(self.config, key, new_value)
        except KeyError:
            pass


class StoredConfiguration(Configuration):
    def __init__(self, config_directory_name, in_production=False):
        self.config_directory = config_directory_name
        self.in_production = in_production

    def configure(self, validate=True):
        self.configure_logging()
        logging.getLogger(__name__).info('Using config in %s' % self.config_directory)
        sys.path.insert(0,self.config_directory)

        assert os.path.isdir(self.config_directory), \
               'no such directory: %s' % self.config_directory

        self.read(ReahlSystemConfig)
        self.validate_required(ReahlSystemConfig)

        require(self.reahlsystem.root_egg)

        self.configure_components()
        if validate:
            self.validate_components()
#        sys.path.remove(self.config_directory)

    def configure_logging(self):
        logging_config_file = os.path.join(self.config_directory, 'logging.conf')
        if os.path.isfile(logging_config_file):
            config.fileConfig(logging_config_file)
        else:
            logging.basicConfig()
        logging.captureWarnings(True)

    def configure_components(self):
        eggs = ReahlEgg.get_all_relevant_interfaces(self.reahlsystem.root_egg)
        for egg in reversed(eggs):
            logging.getLogger(__name__).debug('going to read config for %s' % egg)
            egg.read_config(self)

    def validate_components(self):
        eggs = ReahlEgg.get_all_relevant_interfaces(self.reahlsystem.root_egg)
        for egg in reversed(eggs):
            logging.getLogger(__name__).debug('going to validate config for %s' % egg)
            egg.validate_config(self)

    def list_all(self):
        all_items = []
        all_items.extend(self.list_required(ReahlSystemConfig))
        eggs = ReahlEgg.get_all_relevant_interfaces(self.reahlsystem.root_egg)
        for egg in reversed(eggs):
            all_items.extend(egg.list_config(self))
        return all_items

    def read(self, configuration_class):
        new_config = self.create_config(configuration_class)
        file_path = os.path.join(self.config_directory, new_config.filename)
        if os.path.isfile(file_path):
            locals_dict = ConfigAsDict(self)
            with open(file_path) as f:
                exec(compile(f.read(), file_path, 'exec'), globals(), locals_dict)
            locals_dict.update_required(new_config.config_key)
        else:
            message = 'file "%s" not found, using defaults' % file_path
            logging.getLogger(__name__).info(message)

        unconfigured = self.composite_get_attr(new_config.config_key.split('.'))
        unconfigured.configure() 
        unconfigured.do_injections(self) 

    def create_config(self, configuration_class):
        composite_key = configuration_class.config_key
        keys = composite_key.split('.')
        config = self.composite_get_attr(keys[:-1])
        new_config = configuration_class()
        setattr(config, keys[-1], new_config)
        return new_config

    def validate_required(self, configuration_class):
        composite_key = configuration_class.config_key
        filename = configuration_class.filename
        keys = composite_key.split('.')
        full_filename = os.path.join(self.config_directory, filename)

        try:
            src_config = self.composite_get_attr(keys)
        except AttributeError as e:
            # we make sure that exceptions unrelated to our keys are reraised:
            if set(keys) | set(e.args[0].split()):
                raise ConfigurationException('%s not set in %s' % (composite_key, full_filename))
            else:
                raise

        if not isinstance(src_config, configuration_class):
            raise ConfigurationException('%s is not a %s in %s' % (composite_key, configuration_class, full_filename))

        src_config.validate_contents(full_filename, composite_key, self.in_production)

    def list_required(self, configuration_class):
        composite_key = configuration_class.config_key
        items = []
        keys = composite_key.split('.')

        src_config = self.composite_get_attr(keys)
        if not isinstance(src_config, configuration_class):
            raise ConfigurationException('%s is not a %s in %s' % (composite_key, configuration_class, configuration_class.filename))

        items.extend( src_config.list_contents(configuration_class.filename, composite_key) )
        return items


class CodedConfiguration(StoredConfiguration, dict):
    def __init__(self):
        super(CodedConfiguration, self).__init__('<in memory>')

    def read(self, configuration_class):
        filename = configuration_class.filename
        new_config = self.create_config(configuration_class)
        if filename in self:
            locals_dict = ConfigAsDict(self)
            self[filename](self)
            locals_dict.update_required(new_config.config_key)
        else:
            message = 'key for file "%s" not found, using defaults' % filename
            logging.getLogger(__name__).info(message)

        self.validate_required(configuration_class)


