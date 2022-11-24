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



from reahl.tofu import Fixture, scenario, expected, NoException
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import CallMonitor
from reahl.component.exceptions import IncorrectArgumentError, arg_checks, IsInstance, IsSubclass, \
     ArgumentCheckedCallable, NotYetAvailable
from reahl.component.context import ExecutionContext
from reahl.component.decorators import deprecated
from reahl.component.config import Configuration, ReahlSystemConfig


class ArgumentCheckScenarios(Fixture):
    def new_ModelObject(self):
        class ModelObject:
            @arg_checks(y=IsInstance(int), title=IsInstance(str))
            def do_something(self, x, y, title='a title', style=None):
                pass
        return ModelObject

    @scenario
    def incorrect_positional_arg(self):
        self.expected_exception = IsInstance
        self.args = (1, '2')
        self.call_args = self.args
        self.kwargs = dict(title='some title', style='style')
        self.callable = self.ModelObject().do_something

    @scenario
    def incorrect_kwarg(self):
        self.expected_exception = IsInstance
        self.args = (1, 2)
        self.call_args = self.args
        self.kwargs = dict(title=3, style='style')
        self.callable = self.ModelObject().do_something

    @scenario
    def incorrect_deduced_kwarg(self):
        self.expected_exception = IsInstance
        self.args = (1, 2, 2, 'style')
        self.call_args = self.args
        self.kwargs = {}
        self.callable = self.ModelObject().do_something

    @scenario
    def incorrect_kwarg_not_all_sent(self):
        self.expected_exception = IsInstance
        self.args = (1, 2)
        self.call_args = self.args
        self.kwargs = dict(title=None)
        self.callable = self.ModelObject().do_something

    @scenario
    def correct_args_defaulted_kwargs(self):
        self.expected_exception = NoException
        self.args = (1, 2)
        self.call_args = self.args
        self.kwargs = {}
        self.callable = self.ModelObject().do_something

    @scenario
    def correct_unbound_method_called(self):
        self.expected_exception = NoException
        self.args = (NotYetAvailable('self'), 1, 2)
        self.call_args = (self.ModelObject(), 1, 2)
        self.kwargs = {}
        self.callable = self.ModelObject.do_something

    @scenario
    def correct_function_called(self):
        @arg_checks(y=IsInstance(int), title=IsInstance(str))
        def do_something(x, y, title='a title', style=None):
            pass

        self.expected_exception = NoException
        self.args = (1, 2)
        self.call_args = (1, 2)
        self.kwargs = {}
        self.callable = do_something

    @scenario
    def checks_on_classmethod(self):
        self.expected_exception = IsInstance
        class ModelObject:
            @arg_checks(y=IsInstance(int), title=IsInstance(str))
            @classmethod
            def do_something(cls, x, y, title='a title', style=None):
                pass
        self.args = (1, 'y')
        self.call_args = self.args
        self.kwargs = {}
        self.callable = ModelObject.do_something

    @scenario
    def wrong_args_sent(self):
        self.expected_exception = TypeError
        self.args = (1, 2, 3, 4, 5, 6, 7)
        self.call_args = self.args
        self.kwargs = {}
        self.callable = self.ModelObject().do_something


@with_fixtures(ArgumentCheckScenarios)
def test_checking_arguments(argument_check_fixture):
    """Methods can be augmented with argument checks. These checks are done when calling such a method,
       or before an actual call is made using ArgumentCheckedCallable.checkargs."""
    fixture = argument_check_fixture
    with expected(fixture.expected_exception):
        fixture.callable(*fixture.call_args, **fixture.kwargs)
    with expected(fixture.expected_exception):
        ArgumentCheckedCallable(fixture.callable).checkargs(*fixture.args, **fixture.kwargs)

    wrapped_exception = NoException
    if fixture.expected_exception is not NoException:
        wrapped_exception = IncorrectArgumentError

    with expected(wrapped_exception):
        ArgumentCheckedCallable(fixture.callable, explanation='some message').checkargs(*fixture.args, **fixture.kwargs)

class ArgsCheckDisableFixture(Fixture):

    def new_config(self):
        config = Configuration()
        config.reahlsystem = ReahlSystemConfig()
        return config

    @scenario
    def enable_checks(self):
        self.expected_exception = IsInstance
        self.config.reahlsystem.runtime_checking_enabled = True

    @scenario
    def disable_checks(self):
        self.expected_exception = NoException
        self.config.reahlsystem.runtime_checking_enabled = False


@with_fixtures(ArgsCheckDisableFixture)
def test_disable_argument_checks(args_check_fixture):
    """Config setting overrides executing checks"""

    class ModelObject:
        @arg_checks(y=IsInstance(int))
        def do_something(self, y):
            pass

    with ExecutionContext() as context:
        context.config = args_check_fixture.config

        model_object = ModelObject()
        with expected(args_check_fixture.expected_exception):
            model_object.do_something('5')
        with expected(args_check_fixture.expected_exception):
            ArgumentCheckedCallable(model_object.do_something).checkargs('5')


def test_stubbable_is_instance():
    """Classes can be marked with a flag to let them pass the IsInstance or IsSubclass checks even
       though they do not inherit from the specified class."""

    class A:
        pass

    class B:
        is_A = True

    with expected(NoException):
        assert IsInstance(A).is_valid(B())
    with expected(NoException):
        assert IsSubclass(A).is_valid(B)


def test_checking_before_args_available():
    """When checking arguments before a method call, the checks for some arguments may be ignored by passing NotYetAvailable
       instances for them. The name of NotYetAvailable arguments should match the name of the argument it replaces."""
    class ModelObject:
        @arg_checks(y=IsInstance(int), title=IsInstance(str))
        def do_something(self, x, y, title='a title', style=None):
            pass

    model_object = ModelObject()
    with expected(NoException):
        ArgumentCheckedCallable(model_object.do_something).checkargs('x', NotYetAvailable('y'), title='a title')
    with expected(IsInstance):
        ArgumentCheckedCallable(model_object.do_something).checkargs('x', NotYetAvailable('y'), title=123)

    with expected(IncorrectArgumentError):
        ArgumentCheckedCallable(model_object.do_something, explanation='an explanation').checkargs('x', NotYetAvailable('x'), title='a valid title')


def test_argument_checks_with_deprecated_methods():
    """When used with @deprecated, argument checks still work."""
    @deprecated('this test class is deprecated', '1.2')
    class ADeprecatedClass:
        @arg_checks(y=IsInstance(int), title=IsInstance(str))
        def __init__(self, x, y, title='a title', style=None):
            pass

    with expected(IsInstance):
        ADeprecatedClass(1, 'y')
    with expected(IsInstance):
        ArgumentCheckedCallable(ADeprecatedClass).checkargs('x', 'y')
    with expected(IncorrectArgumentError):
        ArgumentCheckedCallable(ADeprecatedClass, explanation='an explanation').checkargs('x', NotYetAvailable('x'), title='a valid title')


    class ADeprecatedClass:
        @deprecated('this instance method is deprecated', '1.3')
        @arg_checks(y=IsInstance(int), title=IsInstance(str))
        def instance_method(self, x, y, title='a title', style=None):
            pass

        @deprecated('this class method is deprecated', '2.3')
        @arg_checks(y=IsInstance(int), title=IsInstance(str))
        @classmethod
        def class_method(cls, x, y, title='a title', style=None):
            pass

    with expected(IsInstance):
        ADeprecatedClass().instance_method('x', 'y')
    with expected(IsInstance):
        ADeprecatedClass.class_method('x', 'y')
