# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import warnings
import contextlib
import platform
import itertools

import pkg_resources

from reahl.dev.fixtures import ReahlSystemFixture
from reahl.stubble import EmptyStub
from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures
from reahl.component.decorators import deprecated, memoized
from reahl.component.exceptions import arg_checks


@contextlib.contextmanager
def expected_deprecation_warnings(expected_warnings):
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        yield

    warning_messages = [str(i.message) for i in caught_warnings]
    assert len(warning_messages) == len(expected_warnings) 
    for caught, expected_message in itertools.zip_longest(warning_messages, expected_warnings):
        assert expected_message in caught 


class ClassDeprecationScenarios(Fixture):
    @scenario
    def plain_usage(self):
        class ASuperClassWithAnInit:
            def __init__(self): pass
        @deprecated('this test deprecated class is deprecated', '1.2')
        class ADeprecatedClass(ASuperClassWithAnInit):
            @classmethod
            def some_class_method(cls):
                pass
            def some_instance_method(self):
                pass
        self.ADeprecatedClass = ADeprecatedClass

    @scenario
    def used_with_arg_checks(self):
        @deprecated('this test deprecated class is deprecated', '2.3')
        class ADeprecatedClass:
            @arg_checks()
            def __init__(self):
                pass
            
            @arg_checks()
            @classmethod
            def some_class_method(cls):
                pass
            @arg_checks()
            def some_instance_method(self):
                pass
        self.ADeprecatedClass = ADeprecatedClass


@with_fixtures(ReahlSystemFixture, ClassDeprecationScenarios)
def test_deprecating_a_class(reahl_system_fixture, class_deprecation_scenarios):
    """When @deprecated is used on a class, constructing the class or calling class methods 
       emit a deprecation warning. This only works when the Deprecated class has an __init__ or inherits 
       from another class with an __init__."""

    fixture = class_deprecation_scenarios
    with expected_deprecation_warnings(['this test deprecated class is deprecated']):
        deprecated_instance = fixture.ADeprecatedClass()

    with expected_deprecation_warnings([]):
        deprecated_instance.some_instance_method()
        
    with expected_deprecation_warnings(['this test deprecated class is deprecated']):
        fixture.ADeprecatedClass.some_class_method()


def test_deprecating_a_class_docstring():
    """When @deprecated is used, the docstring (if present) of the deprecated class or method is changed to indicate deprecation."""
    
    @deprecated('this is deprecated', '1.2')
    class ClassWithDocstring:
        """A docstring."""
        @deprecated('this also', '0.0')
        def do_something(self):
            """another"""
            pass

    high_python_version = pkg_resources.parse_version(platform.python_version()) > pkg_resources.parse_version('3.6')
    assert not high_python_version or (ClassWithDocstring.__doc__ == 'A docstring.\n\n.. deprecated:: 1.2\n   this is deprecated') 
    assert not high_python_version or (ClassWithDocstring().do_something.__doc__ == 'another\n\n.. deprecated:: 0.0\n   this also') 

    @deprecated('this is deprecated', '1.2')
    class ClassWithoutDocstring:
        pass

    assert not ClassWithoutDocstring.__doc__ 


class MethodDeprecationScenarios(Fixture):
    @scenario
    def plain_usage(self):
        class NonDeprecatedClass:
            @deprecated('this class method is deprecated', '1.1')
            @classmethod
            def some_deprecated_class_method(cls):
                pass
            @classmethod
            def some_class_method(cls):
                pass
            @deprecated('this instance method is deprecated', '4.5')
            def some_deprecated_instance_method(self):
                pass
            def some_instance_method(self):
                pass
        self.NonDeprecatedClass = NonDeprecatedClass

    @scenario
    def used_with_arg_checks(self):
        class NonDeprecatedClass:
            @deprecated('this class method is deprecated', '1.2')
            @arg_checks()
            @classmethod
            def some_deprecated_class_method(cls):
                pass
            @classmethod
            def some_class_method(cls):
                pass
            @deprecated('this instance method is deprecated', '2.3')
            @arg_checks()
            def some_deprecated_instance_method(self):
                pass
            def some_instance_method(self):
                pass
        self.NonDeprecatedClass = NonDeprecatedClass


@with_fixtures(MethodDeprecationScenarios)
def test_deprecating_a_method(method_deprecation_scenarios):
    """When @deprecated is used on a method or classmethod, only calling the method emits a deprecation 
       warning. """

    fixture = method_deprecation_scenarios
    with expected_deprecation_warnings([]):
        fixture.NonDeprecatedClass.some_class_method()

    with expected_deprecation_warnings(['this class method is deprecated']):
        fixture.NonDeprecatedClass.some_deprecated_class_method()

    with expected_deprecation_warnings([]):
        fixture.NonDeprecatedClass().some_instance_method()
        
    with expected_deprecation_warnings(['this instance method is deprecated']):
        fixture.NonDeprecatedClass().some_deprecated_instance_method()


class MemoizeScenarios(Fixture):
    @scenario
    def a_method(self):
        class SomeClass:
            @memoized
            def some_method(self):
              return EmptyStub()

        an_instance = SomeClass()
        self.memoized_callable = an_instance.some_method

    @scenario
    def a_class_method(self):
        class SomeClass:
            @memoized
            @classmethod
            def some_class_method(cls):
              return EmptyStub()

        self.memoized_callable = SomeClass.some_class_method

    @scenario
    def a_class_method_called_via_instance(self):
        class SomeClass:
            @memoized
            @classmethod
            def some_class_method(cls):
              return EmptyStub()

        an_instance = SomeClass()
        self.memoized_callable = an_instance.some_class_method

    @scenario
    def a_function(self):
        @memoized
        def some_function():
          return EmptyStub()

        self.memoized_callable = some_function


@with_fixtures(MemoizeScenarios)
def test_memoize_caches_call_results(memoize_scenarios):
    """On a memoized callable, the result of the first call is cached and re-used on subsequent calls"""

    fixture = memoize_scenarios
    first_call_result = fixture.memoized_callable()
    next_call_result = fixture.memoized_callable()

    assert first_call_result is next_call_result 


def test_memoize_considers_method_args():
    """The results are cached based on the arguments passed to calls."""

    class SomeClass:
        @memoized
        def method_with_args(self, an_arg, a_kwarg=None):
          return EmptyStub()

    an_instance = SomeClass()
    result_with_one_set_of_args = an_instance.method_with_args(123, a_kwarg=1)
    result_with_different_set_of_args = an_instance.method_with_args(456, a_kwarg=1)

    assert result_with_one_set_of_args is not result_with_different_set_of_args 

    second_result_with_same_set_of_args = an_instance.method_with_args(123, a_kwarg=1)

    assert result_with_one_set_of_args is second_result_with_same_set_of_args 


