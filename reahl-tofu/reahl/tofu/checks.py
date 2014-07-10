# Copyright 2005, 2006, 2008-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import inspect
import token
import tokenize
import datetime
import contextlib


#----------------------------------------[ assertion functions ]

class NoExceptionRaised(Exception):
    def __init__(self, expected):
        self.expected = expected
    def __str__(self):
        return '%s was expected' % self.expected

class NoException(Exception):
    """A special exception class used with :func:`expected` to indicate that no exception is
       expected at all.

       For example, the following code will break a test:
       
       .. code-block:: python
       
          with expected(NoException):
              # some code here
              # .....
              # then at some point an exception is raised
              raise AssertionError()
              #.....
    """

@contextlib.contextmanager
def expected(exception, test=None):
    """Returns a context manager that can be used to check that the code in the managed context
       does indeed raise the given exception.

       :param exception: The class of exception to expect
       :keyword test: A function that takes a single argument. Upon catching the expected exception, this\
                      callable is called, passing the exception instance as argument. A programmer can do\
                      more checks on the specific exception instance in this function, such as check its arguments.
                             
       For example, the following code will execute without letting a test break:
       
       .. code-block:: python
       
          with expected(AssertionError):
              # some code here
              # .....
              # then at some point an exception is raised
              raise AssertionError()
              #.....

    """
    if exception is NoException:
        yield
        return

    try:
        yield
    except exception as ex:
        if test:
            test(ex)
    else:
        raise NoExceptionRaised(exception)

def assert_recent(date, seconds_threshold=5, tz=None):
    if date is None:
        is_recent_check = False
    else:
        delta = datetime.datetime.now(tz=tz) - date
        is_recent_check = delta < datetime.timedelta(seconds=seconds_threshold)
    if not is_recent_check:
        if date:
            raise AssertionError( 'Date[%s] exceeds given threshold of %s with %s' % (date, seconds_threshold, delta ) )
        else:
            raise AssertionError( 'No date set' )

def check_limitation(coded_version, msg):
    """Warns that a newer Python version is now used, which may have a fix for
       a limitation which had to be worked around previously.
       
       :param coded_version: The version of Python originally used to write the code being tested. The limitation \
                             is present in this version and the test will only break for newer versions than `coded_version`.
       :param msg: The message to be shown if a newer Python version is used for running the code.


       """

    coded_version_tuple = coded_version.split('.')
    coded_ma, coded_mi = map(int, coded_version_tuple[0:2])

    current_version_tuple = sys.version_info
    current_ma, current_mi = current_version_tuple[0:2]

    assert not( (coded_ma < current_ma) or ((coded_ma == current_ma) and (coded_mi < current_mi)) ), \
           'You are now on python %s.%s, code was written on %s: %s' % \
           (current_ma, current_mi, coded_version, msg)

    
class vassert(object):
    """A replacement for the Python assert statement which shows the values of some variables
       if the assertion fails.
       
       :param expression: A boolean expression. The assertion will fail if this expression does not evaluate to True.

       For example, the following code will yield the stack trace shown below it:

       .. code-block:: python
       
           i = 123
           vassert( i == 1 )

       .. parsed-literal:: 

          AssertionError: vassert( i == 1 )

          ----- values were -----
          i: 123 (<type 'int'>)       
    """
    def find_names(self, source):
        from six.moves import cStringIO
                
        tokens = [ (t[0], t[1])
                   for t in tokenize.generate_tokens(cStringIO(source).readline)
                   if t[0] == token.NAME or t[1] == '.']
        names = []
        concat = False
        for t in tokens:
            if t[0] == token.OP:
                concat = True
            if t[0] == token.NAME:
                if concat:
                    names[-1] = '%s.%s' % (names[-1], t[1])
                else:
                    names.append(t[1])
                concat = False
                
        return names
        
    def __init__(self, expression):
        if __debug__ and not expression:
            try:
                calling_context = inspect.stack()[1]
                calling_frame = calling_context[0]

                [source] = inspect.getframeinfo(calling_frame, 1)[3]
                names = self.find_names(source)
            
                info = {}
                for name in names:
                    elements = name.split('.')
                    if 'vassert' not in elements:
                        first_element = elements[0]
                        if first_element in calling_frame.f_locals \
                               or first_element in calling_frame.f_globals:
                            value = 'could not determine'
                            try:
                                value = eval(name, calling_frame.f_locals, calling_frame.f_globals)
                            except:
                                pass
                            info[name] = value

                message  = '%s\n\n\t----- values were -----\n' % source.strip()
                for i in info.items():
                    message += '\t%s: %s (%s)\n' % (i[0], i[1], type(i[1]))

                raise AssertionError(message)

            finally:
                del calling_frame


