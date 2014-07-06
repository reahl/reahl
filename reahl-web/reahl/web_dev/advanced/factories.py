# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected
from reahl.stubble import EmptyStub

from reahl.component.modelinterface import Field
from reahl.web.fw import Factory, FactoryFromUrlRegex, UserInterface, RegexPath, NoMatchingFactoryFound, UrlBoundView
from reahl.web_dev.fixtures import WebFixture

@istest
class FactoryTests(object):
    @test(Fixture)
    def factory_basics(self, fixture):
        """A Factory can be used to represent a set of parameterised instances instead of having to construct 
           or retrieve all instances.  When a specific instance is needed, the Factory creates (or retrieves) 
           the instance, based on parameters passed."""

        def create_method(arg, kwarg=None):
            instance = EmptyStub()
            instance.arg = arg
            instance.kwarg = kwarg
            return instance

        factory = Factory(create_method)
        instance = factory.create(1, kwarg=2)
        vassert( instance.arg == 1 )
        vassert( instance.kwarg == 2 )


    @test(Fixture)
    def factory_failure_to_create(self, fixture):
        """Parameters sent to .create should identify an instance uniquely and so enable the create_method 
           to construct the correct instance on request. If the create_method cannot create or retrieve 
           an instance using those parameters, it raises NoMatchingFactoryFound to indicate that the asked-for instance 
           does not exist."""

        def create_method(arg, kwarg=None):
            raise NoMatchingFactoryFound()

        factory = Factory(create_method)
        with expected(NoMatchingFactoryFound):
            factory.create(1, kwarg=2)


    @test(Fixture)
    def factory_from_path_regex(self, fixture):
        """An FactoryFromUrlRegex parses args from the given URL and passes these as kwargs to create_method 
           along with the args and kwargs passed to its .create()."""

        def create_method(path, path_arg=None, extra_kwarg=None):
            instance = EmptyStub()
            instance.path_arg = path_arg
            instance.extra_kwarg = extra_kwarg
            return instance

        argument_fields = {'path_arg': Field()}
        factory = FactoryFromUrlRegex(RegexPath('some(?P<path_arg>.+)path', 'some${path_arg}path', argument_fields), create_method, 
                                      dict(extra_kwarg='42'))
        instance = factory.create('somecoolpath')
        vassert( instance.path_arg == 'cool' )
        vassert( instance.extra_kwarg == '42' )


    class MatchingScenarios(WebFixture):
        class ViewWithArg(UrlBoundView):
            def assemble(self, my_one_arg=None): pass

        @scenario
        def slash(self):
            self.matched_path = '/editions'
            self.factory = self.user_interface.define_view('/', title='the view')
            self.is_applicable = False

        @scenario
        def slash_with_subresource(self):
            self.matched_path = '/__a_sub_resource_url'
            self.factory = self.user_interface.define_view('/', title='the view')
            self.is_applicable = True

        @scenario
        def shorter_match_than_discriminator(self):
            self.matched_path = '/editions'
            self.factory = self.user_interface.define_view('/edit', title='the view')
            self.is_applicable = False

        @scenario
        def dynamic_slash_with_args(self):
            self.matched_path = '/editions'
            self.factory = self.user_interface.define_view('/', view_class=self.ViewWithArg, my_one_arg=Field())
            self.is_applicable = True

        @scenario
        def dynamic_slash_with_args_not_enough(self):
            self.matched_path = '/editions/'
            self.factory = self.user_interface.define_view('/', view_class=self.ViewWithArg, my_one_arg=Field())
            self.is_applicable = False

        class UIWithoutKwarg(UserInterface):
            pass

        @scenario
        def parameterised_user_interface_with_long_relative_path(self):
            self.matched_path = '/editions/relative_path'
            self.factory = self.user_interface.define_user_interface('/editions', self.UIWithoutKwarg, {})
            self.is_applicable = True

        @scenario
        def parameterised_user_interface_with_short_relative_path(self):
            self.matched_path = '/editions/'
            self.factory = self.user_interface.define_user_interface('/editions', self.UIWithoutKwarg, {})
            self.is_applicable = True

        @scenario
        def parameterised_user_interface_without_relative_path(self):
            """A user_interface matches an url even if the url does not contain a relative path."""
            self.matched_path = '/editions'
            self.factory = self.user_interface.define_user_interface('/editions', self.UIWithoutKwarg, {})
            self.is_applicable = True

        class UIWithKwarg(UserInterface):
            def assemble(self, my_one_arg=None):
                pass

        @scenario
        def parameterised_user_interface_with_args_and_path(self):
            self.matched_path = '/editions/argument1/'
            self.factory = self.user_interface.define_user_interface('/editions', self.UIWithKwarg, {}, my_one_arg=Field())
            self.is_applicable = True

        @scenario
        def parameterised_user_interface_with_subresources(self):
            self.matched_path = '/editions/argument1/__a_sub_resource'
            self.factory = self.user_interface.define_user_interface('/editions', self.UIWithKwarg, {}, my_one_arg=Field())
            self.is_applicable = True


    @test(MatchingScenarios)
    def matching(self, fixture):
        applicable_rating = fixture.factory.is_applicable_for(fixture.matched_path)
        vassert( (applicable_rating > 0) == fixture.is_applicable )




