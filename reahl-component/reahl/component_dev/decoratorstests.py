# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import warnings
import contextlib
from six.moves import zip_longest

from nose.tools import istest

from reahl.tofu import Fixture, test, scenario, expected, NoException, vassert
from reahl.component.decorators import deprecated
from reahl.component.exceptions import arg_checks

@contextlib.contextmanager
def expected_deprecation_warnings(expected_warnings):
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        yield

    warning_messages = [six.text_type(i.message) for i in caught_warnings]
    vassert( len(warning_messages) == len(expected_warnings) )
    for caught, expected_message in zip_longest(warning_messages, expected_warnings):
        vassert( expected_message in caught )


class ClassDeprecationScenarios(Fixture):
    @scenario
    def plain_usage(self):
        class ASuperClassWithAnInit(object):
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
        class ADeprecatedClass(object):
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


@test(ClassDeprecationScenarios)
def deprecating_a_class(fixture):
    """When @deprecated is used on a class, constructing the class or calling class methods 
       emit a deprecation warning. This only works when the Deprecated class has an __init__ or inherits 
       from another class with an __init__."""
    
    with expected_deprecation_warnings(['this test deprecated class is deprecated']):
        deprecated_instance = fixture.ADeprecatedClass()

    with expected_deprecation_warnings([]):
        deprecated_instance.some_instance_method()
        
    with expected_deprecation_warnings(['this test deprecated class is deprecated']):
        fixture.ADeprecatedClass.some_class_method()


@test(Fixture)
def deprecating_a_class(fixture):
    """When @deprecated is used, the docstring (if present) of the deprecated class or method is changed to indicate deprecation."""
    
    @deprecated('this is deprecated', '1.2')
    class ClassWithDocstring(object):
        """A docstring."""
        @deprecated('this also', '0.0')
        def do_something(self):
            """another"""
            pass

    vassert( six.PY2 or (ClassWithDocstring.__doc__ == 'A docstring.\n.. deprecated:: 1.2\n   this is deprecated') )
    vassert( six.PY2 or (ClassWithDocstring().do_something.__doc__ == 'another\n.. deprecated:: 0.0\n   this also') )

    @deprecated('this is deprecated', '1.2')
    class ClassWithoutDocstring(object):
        pass

    vassert( not ClassWithoutDocstring.__doc__ )



class MethodDeprecationScenarios(Fixture):
    @scenario
    def plain_usage(self):
        class NonDeprecatedClass(object):
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
        class NonDeprecatedClass(object):
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

@test(MethodDeprecationScenarios)
def deprecating_a_method(fixture):
    """When @deprecated is used on a method or classmethod, only calling the method emits a deprecation 
       warning. """
    
    with expected_deprecation_warnings([]):
        fixture.NonDeprecatedClass.some_class_method()

    with expected_deprecation_warnings(['this class method is deprecated']):
        fixture.NonDeprecatedClass.some_deprecated_class_method()

    with expected_deprecation_warnings([]):
        fixture.NonDeprecatedClass().some_instance_method()
        
    with expected_deprecation_warnings(['this instance method is deprecated']):
        fixture.NonDeprecatedClass().some_deprecated_instance_method()

