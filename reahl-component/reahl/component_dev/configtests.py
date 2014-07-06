# Copyright 2008-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
import six
import pkg_resources
import re
import logging

from pkg_resources import DistributionNotFound
from nose.tools import istest

from reahl.tofu import test
from reahl.tofu import Fixture
from reahl.tofu import set_up
from reahl.tofu import vassert, temp_dir, expected
from reahl.stubble import CallMonitor
from reahl.stubble import EasterEgg
from reahl.stubble import easter_egg

from reahl.component.eggs import ReahlEgg
from reahl.component.config import Configuration, StoredConfiguration, ConfigSetting, \
                                   ConfigurationException, EntryPointClassList


class ConfigWithFiles(Fixture):
    def new_config_dir(self):
        return temp_dir()
    
    def new_config_bootstrap_file(self):
        contents = """
reahlsystem.root_egg = '%s'
reahlsystem.connection_uri = None
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
        ReahlEgg.clear_cache()

    def set_config_spec(self, egg, code_locator_string):
        line = 'config = %s' % code_locator_string
        egg.add_entry_point_from_line('reahl.configspec', line)

        line = 'Egg = reahl.component.eggs:ReahlEgg' 
        egg.add_entry_point_from_line('reahl.eggs', line)



class ConfigWithSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting()


@istest
class ConfigTests1(object):
    @test(ConfigWithFiles)
    def config_basics(self, fixture):
        """Config is specified per component, via its ReahlEgg interface, and read from its own config file."""

        config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                              contents='some_key.some_setting = 3')
        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        config.configure()
        
        # The setting was read
        vassert( config.some_key.some_setting == 3 )

    @test(ConfigWithFiles)
    def missing_settings(self, fixture):
        """An exception is raised if setting do not have values set."""

        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        
        with expected(ConfigurationException):
            config.configure()

    @test(ConfigWithFiles)
    def incorrect_settings(self, fixture):
        """An exception is raised when an attempt is made to set a setting that does not exist."""

        config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                              contents='some_key.some_wrong_name = 3')
        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        
        with expected(ConfigurationException):
            config.configure()

    @test(ConfigWithFiles)
    def incorrect_replacement_of_configuration(self, fixture):
        """An exception is raised when an attempt is made to replace a Configuration with another of the wrong type."""

        config_file = fixture.new_config_file(filename=ConfigWithSetting.filename, 
                                              contents='from reahl.component.config import Configuration; some_key = Configuration()')
        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        
        with expected(ConfigurationException):
            config.configure()


class ConfigWithDefaultedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting(default='default value')

@istest
class ConfigTests2(object):
    @test(ConfigWithFiles)
    def config_defaults(self, fixture):
        """If a default is specified for the ConfigSetting, it need not be set in the file."""

        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithDefaultedSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        config.configure()
        
        # The setting was read
        vassert( config.some_key.some_setting == 'default value' )


class ConfigWithDangerousDefaultedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = ConfigSetting(default='default value', dangerous=True)

    
@istest
class ConfigTests3(object):
    @test(ConfigWithFiles)
    def config_defaults(self, fixture):
        """Defaults that are dangerous to leave at their at their settings can be marked as such. 
           This will result in a logged warning."""

        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithDangerousDefaultedSetting')

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        with CallMonitor(logging.getLogger('reahl.component.config').warning) as monitor:
            config.configure()

        # A warning was issued with warn severity to the log
        logged_message = monitor.calls[0].args[0]
        message_regex = 'some_key.some_setting in /.*/config_file_for_this_egg.py is using a dangerous default setting'
        vassert( re.match(message_regex, logged_message) )
        
        # The default value is still used
        vassert( config.some_key.some_setting == 'default value' )

    @test(ConfigWithFiles)
    def config_in_production(self, fixture):
        """When a Configuration is created as in_production, dangerous defaulted config is not allowed."""

        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithDangerousDefaultedSetting')

        config = StoredConfiguration(fixture.config_dir.name, in_production=True)
        with expected(ConfigurationException):
            config.configure()

    class DistributionNotFoundConfig(ConfigWithFiles):
        def new_root_egg_name(self):
            return 'missing_root_egg'

    @test(DistributionNotFoundConfig)
    def hint_on_distribution_not_found(self, fixture):
        """When a DistributionNotFoundException is raised - in development ONLY - for the current root_egg,
           its message is augmented with a hint for new users."""

        # Case: development
        config = StoredConfiguration(fixture.config_dir.name, in_production=False)
        
        def check_exception(ex):
            vassert( six.text_type(ex) == 'missing-root-egg (It looks like you are in a development environment. Did you run "reahl setup -- develop -N"?)' )

        with expected(DistributionNotFound, test=check_exception):
            config.configure()

        # Case: production
        config = StoredConfiguration(fixture.config_dir.name, in_production=True)
        
        def check_exception(ex):
            vassert( six.text_type(ex) == 'missing-root-egg' )

        with expected(DistributionNotFound, test=check_exception):
            config.configure()




class ConfigWithEntryPointClassList(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    some_setting = EntryPointClassList('some.test.entrypoint', description='we test stuff')


class ListedClass1(object): pass
class ListedClass2(object): pass

@istest
class ConfigTests4(object):
    @test(ConfigWithFiles)
    def entry_point_class_list(self, fixture):
        """EntryPointClassList is a special ConfigSetting which reads its value from a pkg_resources
           entry point which contains a list of classes published by any (possibly other) egg."""
        # Because we cannot remove EasterEggs from pkg_resources, the next test must happen after
        # this one. The next check just ensures that we know when that does not happen:
        with expected(pkg_resources.DistributionNotFound):
            pkg_resources.require('test-inject')  
            
        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWithEntryPointClassList')

        # Publish some classes on the entry point being tested
        line = 'ListedClass1 = reahl.component_dev.configtests:ListedClass1'
        easter_egg.add_entry_point_from_line('some.test.entrypoint', line)
        line = 'ListedClass2 = reahl.component_dev.configtests:ListedClass2'
        easter_egg.add_entry_point_from_line('some.test.entrypoint', line)

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        config.configure()

        # The classes are found from the entry point
        vassert( set(config.some_key.some_setting) == {ListedClass1, ListedClass2} )



class ConfigWithInjectedSetting(Configuration):
    filename = 'config_file_for_this_egg.py'
    config_key = 'some_key'
    injected_setting = ConfigSetting(automatic=True)


class ConfigWhichInjectsSetting(Configuration):
    filename = 'injector_egg.py'
    config_key = 'some_other_key'
    def do_injections(self, config):
        config.some_key.injected_setting = 123

@istest
class ConfigTests5(object):
    @test(ConfigWithFiles)
    def config_defaults(self, fixture):
        """To facilitate dependency injection, the Configuration of one Egg can set the 'automatic' ConfigSettings of
           another egg on which it depends."""

        egg_needing_injection = EasterEgg('test-inject')
        fixture.set_config_spec(egg_needing_injection, 'reahl.component_dev.configtests:ConfigWithInjectedSetting')
        pkg_resources.working_set.add(egg_needing_injection)

        fixture.set_config_spec(easter_egg, 'reahl.component_dev.configtests:ConfigWhichInjectsSetting')

        easter_egg.add_dependency(egg_needing_injection.as_requirement_string())

        # Usually this happens inside other infrastructure, such as the implementation of reahl serve (see reahl-dev)
        config = StoredConfiguration(fixture.config_dir.name)
        config.configure()

        # The default value is still used
        vassert( config.some_key.injected_setting == 123 )







