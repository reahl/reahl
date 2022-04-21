# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import pkg_resources
import re
import logging

from reahl.tofu import Fixture, set_up, temp_dir, expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import CallMonitor, EasterEgg, easter_egg

from reahl.component.eggs import ReahlEgg
from reahl.component.config import Configuration, StoredConfiguration, ConfigSetting, \
                                   ConfigurationException, EntryPointClassList, DeferredDefault


class ConfigWithFiles(Fixture):
    def new_config_dir(self):
        return temp_dir()
    
    def new_config_bootstrap_file(self):
        contents = """
reahlsystem.root_egg = '%s'
reahlsystem.connection_uri = None
reahlsystem.debug = False
""" % self.root_egg_name
        return self.new_config_file(filename='reahl.config.py', contents=contents)

    def new_root_egg_name(self):
        return easter_egg.as_requirement_string()

    def new_config_file_name(self):
        return 'some_file.py'
        
    def new_config_file(self, filename=None, contents=''):
        return self.config_dir.file_with(filename or self.config_file_name, contents)
        
    @set_up
    def set_up_easter_egg(self):
        self.config_bootstrap_file
        easter_egg.clear()
        easter_egg.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"'
        ReahlEgg.clear_cache()

    def set_config_spec(self, egg, code_locator_string):
        egg.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"\nconfiguration = "%s"' % code_locator_string



class ConfigWithSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting()


@with_fixtures(ConfigWithFiles)
def test_config_basics(config_with_files):
    """Config is specified per component, via its ReahlEgg interface, and read from its own config file."""

    fixture = config_with_files
    config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                          contents='some_key.some_setting = 3')
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    config.configure()

    # The setting was read
    assert config.some_key.some_setting == 3 


@with_fixtures(ConfigWithFiles)
def test_missing_settings(config_with_files):
    """An exception is raised if setting do not have values set."""
    fixture = config_with_files
    
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)

    with expected(ConfigurationException):
        config.configure()


@with_fixtures(ConfigWithFiles)
def test_incorrect_settings(config_with_files):
    """An exception is raised when an attempt is made to set a setting that does not exist."""

    fixture = config_with_files
    config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                          contents='some_key.some_wrong_name = 3')
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)

    with expected(ConfigurationException):
        config.configure()


@with_fixtures(ConfigWithFiles)
def test_incorrect_replacement_of_configuration(config_with_files):
    """An exception is raised when an attempt is made to replace a Configuration with another of the wrong type."""

    fixture = config_with_files
    config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                          contents='from reahl.component.config import Configuration; some_key = Configuration()')
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)

    with expected(ConfigurationException):
        config.configure()


class ConfigWithDefaultedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting(default='default value')


@with_fixtures(ConfigWithFiles)
def test_config_defaults(config_with_files):
    """If a default is specified for the ConfigSetting, it need not be set in the file."""

    fixture = config_with_files
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithDefaultedSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    config.configure()

    # The setting was read
    assert config.some_key.some_setting == 'default value' 


class ConfigWithDangerousDefaultedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting(default='default value', dangerous=True)


@with_fixtures(ConfigWithFiles)
def test_config_defaults_dangerous(config_with_files):
    """Defaults that are dangerous to leave at their at their settings can be marked as such. 
       This will result in a logged warning."""

    fixture = config_with_files
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithDangerousDefaultedSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    with CallMonitor(logging.getLogger('reahl.component.config').warning) as monitor:
        config.configure()

    # A warning was issued with warn severity to the log
    logged_message = monitor.calls[0].args[0]
    message_regex = '^some_key.some_setting has been defaulted to a value not suitable for production use: "default value". You can set it in /.*/config_file_for_this_egg.py'
    assert re.match(message_regex, logged_message)

    # The default value is still used
    assert config.some_key.some_setting == 'default value' 


@with_fixtures(ConfigWithFiles)
def test_config_strict_checking(config_with_files):
    """When a Configuration is created with strict_checking=True, dangerous defaulted config is not allowed."""

    fixture = config_with_files
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithDangerousDefaultedSetting')

    config = StoredConfiguration(fixture.config_dir.name, strict_checking=True)
    with expected(ConfigurationException):
        config.configure()


class ConfigWithEntryPointClassList(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = EntryPointClassList('some.test.entrypoint', description='we test stuff')


class ListedClass1: pass
class ListedClass2: pass


@with_fixtures(ConfigWithFiles)
def test_entry_point_class_list(config_with_files):
    """EntryPointClassList is a special ConfigSetting which reads its value from a pkg_resources
       entry point which contains a list of classes published by any (possibly other) egg."""
    fixture = config_with_files
    
    # Because we cannot remove EasterEggs from pkg_resources, the next test must happen after
    # this one. The next check just ensures that we know when that does not happen:
    with expected(pkg_resources.DistributionNotFound):
        pkg_resources.require('test-inject')  

    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithEntryPointClassList')

    # Publish some classes on the entry point being tested
    line = 'ListedClass1 = reahl.component_dev.test_config:ListedClass1'
    easter_egg.add_entry_point_from_line('some.test.entrypoint', line)
    line = 'ListedClass2 = reahl.component_dev.test_config:ListedClass2'
    easter_egg.add_entry_point_from_line('some.test.entrypoint', line)

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    config.configure()

    # The classes are found from the entry point
    assert set(config.some_key.some_setting) == {ListedClass1, ListedClass2} 


class ConfigWithInjectedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    injected_setting = ConfigSetting(automatic=True)


class ConfigWhichInjectsSetting(Configuration):
    filename = 'injector_egg.py'
    config_key = 'some_other_key'

    def do_injections(self, config):
        config.some_key.injected_setting = 123


@with_fixtures(ConfigWithFiles)
def test_config_defaults_automatic(config_with_files):
    """To facilitate dependency injection, the Configuration of one Egg can set the 'automatic' ConfigSettings of
       another egg on which it depends."""

    fixture = config_with_files
    
    egg_needing_injection = EasterEgg('test-inject')
    fixture.set_config_spec(egg_needing_injection, 'reahl.component_dev.test_config:ConfigWithInjectedSetting')
    pkg_resources.working_set.add(egg_needing_injection)

    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWhichInjectsSetting')

    easter_egg.add_dependency(egg_needing_injection.as_requirement_string())

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    config.configure()

    # The default value is still used
    assert config.some_key.injected_setting == 123 


class ConfigWithDependentSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting(default='default value')
    some_other_setting = ConfigSetting(default=DeferredDefault(lambda c: 'tra %s lala' % c.some_setting))


@with_fixtures(ConfigWithFiles)
def test_config_dependent_defaults(config_with_files):
    """The default of one setting can be dependent on another setting if passed a callable"""
    
    fixture = config_with_files
    fixture.set_config_spec(easter_egg, 'reahl.component_dev.test_config:ConfigWithDependentSetting')

    # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
    config = StoredConfiguration(fixture.config_dir.name)
    config.configure()

    # The setting was read
    assert config.some_key.some_setting == 'default value' 
    assert config.some_key.some_other_setting == 'tra default value lala' 

    
