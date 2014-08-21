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
import sys
from contextlib import contextmanager

from reahl.stubble.stub import StubClass


class SystemOutStub(object):
    """The SystemOutStub can be used as context manager to test output that some code
       sends to sys.stdout. 

       For example, the following code does not output anything to the console:

       .. code-block:: python

          with SystemOutStub() as monitor:
              print('hello')

          assert monitor.captured_output == 'hello\\n'

    """
    def __init__(self):
        self.captured_output = '' #: The output captured during the time the SystemOutStub was active.

    def write(self, output):
        self.captured_output += output
        
    def __enter__(self):
        self.original_stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exception_type, value, traceback):
        sys.stdout = self.original_stdout

    def capture_console_screenshot(self, filename):
        with open(filename, 'wb') as output_file:
            output_file.write(self.captured_output)


class MonitoredCall(object):
    """The record of one call that was made to a method. This class is not intended to be 
       instantiated by a programmer. Programmers can query instances of MonitoredCall
       returned by a :class:`CallMonitor` or :class:`InitMonitor`."""
    def __init__(self, args, kwargs, return_value):
        self.return_value = return_value #: The value returned by the call
        self.args = args #: The tuple with positional arguments passed during the call
        self.kwargs = kwargs #: The dictionary with keyword arguments passed during the call

        
class CallMonitor(object):
    """The CallMonitor is a context manager which records calls to a single method of an object or class.
       The calls are recorded, but the original method is also executed.

       For example:

       .. code-block:: python
       
          class SomeClass(object):
              def foo(self, arg):
                  return 'something'

          s = SomeClass()

          with CallMonitor(s.foo) as monitor:
              assert s.foo('a value') == 'something'

          assert monitor.times_called == 1
          assert monitor.calls[0].args == ('a value',)
          assert monitor.calls[0].kwargs == {}
          assert monitor.calls[0].return_value == 'something'
    """
    def __init__(self, method):
        self.obj = method.__self__
        self.method_name = method.__func__.__name__
        self.calls = []  #: A list of :class:`MonitoredCalls` made, one for each call made, in the order they were made
        self.original_method = None

    @property
    def times_called(self):
        """The number of calls that were made during the time the CallMonitor was active."""
        return len(self.calls)

    def monitor_call(self, *args, **kwargs):
        return_value = self.original_method(*args, **kwargs)
        self.calls.append( MonitoredCall(args, kwargs, return_value) )
        return return_value
                
    def __enter__(self):
        self.original_method = getattr(self.obj, self.method_name)
        setattr(self.obj, self.method_name, self.monitor_call)
        return self

    def __exit__(self, exception_type, value, traceback):
        setattr(self.obj, self.method_name, self.original_method)


class InitMonitor(CallMonitor):
    """A :class:`CallMonitor` used to intercept calls to the __init__ method
       of a class."""
    def __init__(self, monitored_class):
        super(InitMonitor, self).__init__(monitored_class.__init__)
        self.obj = monitored_class

    @property
    def monitored_class(self):
        return self.obj

    def monitor_call(self, *args, **kwargs):
        bound_args = (self.instance,)+args
        self.original_method(*bound_args, **kwargs)
        self.calls.append( MonitoredCall(args, kwargs, self.instance) )

    def modified_new(self, *args, **kwargs):
        self.instance = self.original_new(*args, **kwargs)
        return self.instance
    
    def __enter__(self):
        super(InitMonitor, self).__enter__()
        self.original_new = getattr(self.obj, '__new__')
        setattr(self.obj, '__new__', self.modified_new)
        return self

    def __exit__(self, exception_type, value, traceback):
        super(InitMonitor, self).__exit__(exception_type, value, traceback)
        setattr(self.obj, '__new__', self.original_new)


@contextmanager
def replaced(method, replacement):
    """A context manager which replaces the method passed in as `method` with the callable
       in `replacement` for the duration of the managed context.

       .. code-block:: python

          class SomethingElse(object):
              def foo(self, n, y='yyy'):
                  assert None, 'This should never be reached in this test'

          s = SomethingElse()

          def replacement(n, y=None):
              return y

          with replaced(s.foo, replacement):
              assert s.foo(1, y='a') == 'a'
              assert s.foo(2) == None

          assert s.foo(2) == 'yyy'
    """
    StubClass.signatures_match(method, replacement, ignore_self=True)
    target = method.im_self or method.im_class
    method_name = method.im_func.__name__
    saved_method = getattr(target, method_name)
    try:
        setattr(target, method_name, replacement)
        yield
    finally:
        setattr(target, method_name, saved_method)


    
        
