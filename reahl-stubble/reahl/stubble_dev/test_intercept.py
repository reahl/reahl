# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import io
import tempfile

import pytest
from reahl.stubble import CallMonitor, InitMonitor, SystemOutStub, replaced


def test_monitor():
    """A CallMonitor records each call to a method, and its arguments."""

    class SomethingElse:
        def foo(self, n, y=None):
            self.n = n
            return y

    s = SomethingElse()
    original_method = s.foo.__func__

    with CallMonitor(s.foo) as monitor:
        assert s.foo(1, y='a') == 'a'
        assert s.foo(2) is None

    assert s.foo.__func__ is original_method
    assert s.n == 2
    assert monitor.times_called == 2
    assert monitor.calls[0].args == (1,)
    assert monitor.calls[0].kwargs == {'y':'a'}
    assert monitor.calls[0].return_value == 'a'

    assert monitor.calls[1].args == (2,)
    assert monitor.calls[1].kwargs == {}
    assert monitor.calls[1].return_value is None


def test_monitor_class_methods():
    """A CallMonitor works for class methods as well."""

    class SomethingElse:
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



def test_init_monitor():
    """An InitMonitor can monitor calls to __init__."""

    class SomethingElse:
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


def test_replace():
    """Replaced methods replace the original one, but are restored after the with."""

    class SomethingElse:
        def foo(self, n, y=None):
            assert None, 'This should never be reached in this test'


    # Case: bound method
    s = SomethingElse()
    def replacement(n, y=None):
        return y
    original_method = s.foo.__func__

    with replaced(s.foo, replacement):
        assert s.foo(1, y='a') == 'a'
        assert s.foo(2) is None

    assert s.foo.__func__ is original_method

    # Case: unbound method
    """Python 3 does not support the concept of unbound methods, they are
    just plain functions without an im_class pointing back to their class.
    See https://docs.python.org/3/whatsnew/3.0.html#operators-and-special-methods,
    and https://mail.python.org/pipermail/python-dev/2005-January/050625.html
    for the rationale.

    To be able to support them under Python3, on= is mandatory.
    """

    s = SomethingElse()
    def replacement(self, n, y=None):
        return y

    original_method = SomethingElse.foo

    with replaced(SomethingElse.foo, replacement, on=SomethingElse):
        assert s.foo(1, y='a') == 'a'
        assert s.foo(2) is None

    restored_method = SomethingElse.foo
    assert restored_method is original_method

    # Case: unbound method (no on= given)
    s = SomethingElse()
    def replacement(self, n, y=None):
        return y

    with pytest.raises(ValueError, match='You have to supply a on= when stubbing an unbound method'):
        with replaced(SomethingElse.foo, replacement):
            pass

def test_replacing_functions_is_disallowed():
    """Functions can not be replaced, only methods can."""

    def function1():
        pass
    def function2():
        pass

    with pytest.raises(ValueError):
        with replaced(function1, function2):
            pass


def test_replaced_signature_should_match():
    """Replacing methods should have the same signature as the ones they replace."""

    class SomethingElse:
        def foo(self, n, y=None):
            assert None, 'This should never be reached in this test'

    s = SomethingElse()

    def replacement():
        pass

    with pytest.raises(AssertionError):
        with replaced(s.foo, replacement):
            pass


def test_stubbed_sysout():
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



