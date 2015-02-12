# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division
import six

from nose.tools import istest

from reahl.tofu import Fixture, test, scenario, expected, NoException, vassert
from reahl.component.exceptions import ArgumentCheck, IncorrectArgumentError, arg_checks, IsInstance, IsSubclass, checkargs, checkargs_explained, NotYetAvailable
from reahl.component.decorators import deprecated

@istest
class ArgumentCheckTests(object):
    class ArgumentCheckScenarios(Fixture):
        def new_model_object(self):
            class ModelObject(object):
                @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
                def do_something(self, x, y, title='a title', style=None):
                    pass
            return ModelObject()
            
        def new_callable(self):
            return self.model_object.do_something
            
        @scenario
        def incorrect_positional_arg(self):
            self.expected_exception = IsInstance
            self.args = (1, '2')
            self.kwargs = dict(title='some title', style='style')

        @scenario
        def incorrect_kwarg(self):
            self.expected_exception = IsInstance
            self.args = (1, 2)
            self.kwargs = dict(title=3, style='style')

        @scenario
        def incorrect_deduced_kwarg(self):
            self.expected_exception = IsInstance
            self.args = (1, 2, 2, 'style')
            self.kwargs = {}

        @scenario
        def incorrect_kwarg_not_all_sent(self):
            self.expected_exception = IsInstance
            self.args = (1, 2)
            self.kwargs = dict(title=None)

        @scenario
        def correct_args_defaulted_kwargs(self):
            self.expected_exception = NoException
            self.args = (1, 2)
            self.kwargs = {}

        @scenario
        def checks_on_classmethod(self):
            self.expected_exception = IsInstance
            class ModelObject(object):
                @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
                @classmethod
                def do_something(cls, x, y, title='a title', style=None):
                    pass
            self.args = (1, 'y')
            self.kwargs = {}
            self.callable = ModelObject.do_something

        @scenario
        def wrong_args_sent(self):
            self.expected_exception = TypeError
            self.args = (1, 2, 3, 4, 5, 6, 7)
            self.kwargs = {}


    @test(ArgumentCheckScenarios)
    def checking_arguments(self, fixture):
        """Methods can be augmented with argument checks. These checks are done when calling such a method,
           or via checkargs or checkargs_explained before an actual call is made."""

        with expected(fixture.expected_exception):
            fixture.callable(*fixture.args, **fixture.kwargs)
        with expected(fixture.expected_exception):
            checkargs(fixture.callable, fixture.args, fixture.kwargs)


        wrapped_exception = NoException
        if fixture.expected_exception is not NoException:
            wrapped_exception = IncorrectArgumentError

        with expected(wrapped_exception):
            checkargs_explained('some message', fixture.callable, fixture.args, fixture.kwargs)


    @test(Fixture)
    def stubbable_is_instance(self, fixture):
        """Classes can be marked with a flag to let them pass the IsInstance or IsSubclass checks even
           though they do not inherit from the specified class."""
           
        class A(object):
            pass
            
        class B(object):
            is_A = True
            
        with expected(NoException):
            vassert( IsInstance(A).is_valid(B()) )
        with expected(NoException):
            vassert( IsSubclass(A).is_valid(B) )
    
    @test(Fixture)
    def checking_before_args_available(self, fixture):
        """When checking arguments before a method call, the checks for some arguments may be ignored by passing NotYetAvailable
           instances for them. The name of NotYetAvailable arguments should match the name of the argument it replaces."""
        class ModelObject(object):
            @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
            def do_something(self, x, y, title='a title', style=None):
                pass
                
        model_object = ModelObject()
        with expected(NoException):
            checkargs(model_object.do_something, ('x', NotYetAvailable('y')), dict(title='a title'))
        with expected(IsInstance):
            checkargs(model_object.do_something, ('x', NotYetAvailable('y')), dict(title=123))

        with expected(IncorrectArgumentError):
            checkargs_explained('an explanation', model_object.do_something, ('x', NotYetAvailable('x')), dict(title='a valid title'))



@test(Fixture)
def argument_checks_with_deprecated_methods(fixture):
    """When used with @deprecated, argument checks still work."""
    @deprecated('this test class is deprecated')
    class ADeprecatedClass(object):
        @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
        def __init__(self, x, y, title='a title', style=None):
            pass

    with expected(IsInstance):
        ADeprecatedClass(1, 'y')
    with expected(IsInstance):
        checkargs(ADeprecatedClass, ('x', 'y'), {})
    with expected(IncorrectArgumentError):
        checkargs_explained('an explanation', ADeprecatedClass, ('x', NotYetAvailable('x')), dict(title='a valid title'))


    class ADeprecatedClass(object):
        @deprecated('this instance method is deprecated')
        @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
        def instance_method(self, x, y, title='a title', style=None):
            pass

        @deprecated('this class method is deprecated')
        @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
        @classmethod
        def class_method(cls, x, y, title='a title', style=None):
            pass

    with expected(IsInstance):
        ADeprecatedClass().instance_method('x', 'y')
    with expected(IsInstance):
        ADeprecatedClass.class_method('x', 'y')
