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

import io
import six
import warnings
from nose.tools import istest, assert_raises
import tempfile

from reahl.stubble import CallMonitor, InitMonitor, SystemOutStub, replaced

@istest
class InterceptTests(object):
    @istest
    def test_monitor(self):
        """A CallMonitor records each call to a method, and its arguments."""

        class SomethingElse(object):
            def foo(self, n, y=None):
                self.n = n
                return y

        s = SomethingElse()
        original_method = six.get_method_function(s.foo)

        with CallMonitor(s.foo) as monitor:
            assert s.foo(1, y='a') == 'a'
            assert s.foo(2) == None

        assert six.get_method_function(s.foo) is original_method
        assert s.n == 2
        assert monitor.times_called == 2
        assert monitor.calls[0].args == (1,)
        assert monitor.calls[0].kwargs == {'y':'a'}
        assert monitor.calls[0].return_value == 'a'

        assert monitor.calls[1].args == (2,)
        assert monitor.calls[1].kwargs == {}
        assert monitor.calls[1].return_value == None

    @istest
    def test_monitor_class_methods(self):
        """A CallMonitor works for class methods as well."""

        class SomethingElse(object):
            @classmethod
            def foo(cls):
                return cls

        original_method = SomethingElse.foo

        with CallMonitor(SomethingElse.foo) as monitor:
            cls = SomethingElse.foo()
            assert cls is SomethingElse

        assert SomethingElse.foo == original_method
        assert monitor.times_called == 1
        assert monitor.calls[0].args == ()
        assert monitor.calls[0].return_value == SomethingElse


    @istest
    def test_init_monitor(self):
        """An InitMonitor can monitor calls to __init__."""

        class SomethingElse(object):
            def __init__(self):
                self.initialised = True

        original_method = SomethingElse.__init__

        with InitMonitor(SomethingElse) as monitor:
            s = SomethingElse()
            assert isinstance(s, SomethingElse)
            assert s.initialised == True

        assert SomethingElse.__init__ == original_method
        assert monitor.times_called == 1
        assert monitor.calls[0].args == ()
        assert monitor.calls[0].return_value is s

    @istest
    def test_replace(self):
        """Replaced methods replace the original one, but are restored after the with."""
        
        class SomethingElse(object):
            def foo(self, n, y=None):
                assert None, 'This should never be reached in this test'


        # Case: bound method
        s = SomethingElse()
        def replacement(n, y=None):
            return y
        original_method = six.get_method_function(s.foo)

        with replaced(s.foo, replacement):
            assert s.foo(1, y='a') == 'a'
            assert s.foo(2) == None

        assert six.get_method_function(s.foo) is original_method

        # Case: unbound method
        """Python 3 does not support the concept of unbound methods, they are
        just plain functions without an im_class pointing back to their class.
        See https://docs.python.org/3/whatsnew/3.0.html#operators-and-special-methods,
        and https://mail.python.org/pipermail/python-dev/2005-January/050625.html
        for the rationale.

        If stubble wishes to support them under Python 3, the signature of
        stubble.replaced will need to change to take the class as a parameter.
        But since reahl itself does not use this feature, we just deprecate
        it under Python 2 and make it illegal under Python 3.

        Note that we are only talking about instance methods here, not class
        methods. Instance methods always require an instance to be called on, so
        there should always be an instance they can be stubbed on, i.e. by using
        replaced(instance.method, ...) instead of replaced(someclass.method, ...).
        """

        s = SomethingElse()
        def replacement(self, n, y=None):
            return y
        if six.PY2:
            original_method = six.get_method_function(SomethingElse.foo)

            with warnings.catch_warnings(record=True) as raised_warnings:
                warnings.simplefilter("always")
                with replaced(SomethingElse.foo, replacement):
                    assert s.foo(1, y='a') == 'a'
                    assert s.foo(2) == None
                    assert six.get_method_function(SomethingElse.foo) is not original_method
            assert six.get_method_function(SomethingElse.foo) is original_method

            [deprecation] = raised_warnings
            assert issubclass(deprecation.category, DeprecationWarning)
        else:
            with assert_raises(ValueError):
                with replaced(SomethingElse.foo, replacement):
                    pass

    @istest
    def test_replacing_functions_is_disallowed(self):
        """Functions can not be replaced, only methods can."""

        def function1():
            pass
        def function2():
            pass

        with assert_raises(ValueError):
            with replaced(function1, function2):
                pass

    @istest
    def test_replaced_signature_should_match(self):
        """Replacing methods should have the same signature as the ones they replace."""
        
        class SomethingElse(object):
            def foo(self, n, y=None):
                assert None, 'This should never be reached in this test'


        s = SomethingElse()

        def replacement():
            pass

        with assert_raises(AssertionError):
            with replaced(s.foo, replacement):
                pass

    @istest
    def test_stubbed_sysout(self):
        """A SystemOutStub can be used to capture console output. Such output can be captured as a "textual screenshot"."""

        def print_something():
            print('something')
            print('printed')
            
        with SystemOutStub() as output:
            print_something()

        assert output.captured_output == 'something\nprinted\n'

        screenshot_filename = tempfile.mktemp()
        output.capture_console_screenshot(screenshot_filename)

        with io.open(screenshot_filename,'r') as screenshot:
            assert( screenshot.read() == output.captured_output )



