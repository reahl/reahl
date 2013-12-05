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
        original_method = s.foo.im_func

        with CallMonitor(s.foo) as monitor:
            assert s.foo(1, y=u'a') == u'a'
            assert s.foo(2) == None

        assert s.foo.im_func is original_method
        assert s.n == 2
        assert monitor.times_called == 2
        assert monitor.calls[0].args == (1,)
        assert monitor.calls[0].kwargs == {u'y':u'a'}
        assert monitor.calls[0].return_value == u'a'

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
                assert None, u'This should never be reached in this test'


        s = SomethingElse()
        original_method = s.foo.im_func

        def replacement(n, y=None):
            return y

        with replaced(s.foo, replacement):
            assert s.foo(1, y=u'a') == u'a'
            assert s.foo(2) == None

        assert s.foo.im_func is original_method

    @istest
    def test_replaced_signature_should_match(self):
        """Replacing methods should have the same signature as the ones they replace."""
        
        class SomethingElse(object):
            def foo(self, n, y=None):
                assert None, u'This should never be reached in this test'


        s = SomethingElse()
        original_method = s.foo.im_func

        def replacement():
            return y

        def with_statement():
            with replaced(s.foo, replacement):
                pass
        
        assert_raises(AssertionError, with_statement)

    @istest
    def test_stubbed_sysout(self):
        """A SystemOutStub can be used to capture console output. Such output can be captured as a "textual screenshot"."""

        def print_something():
            print u'something'
            print u'printed'
            
        with SystemOutStub() as output:
            print_something()

        assert output.captured_output == u'something\nprinted\n'

        screenshot_filename = tempfile.mktemp()
        output.capture_console_screenshot(screenshot_filename)

        with open(screenshot_filename,'r') as screenshot:
            assert( screenshot.read() == output.captured_output )



