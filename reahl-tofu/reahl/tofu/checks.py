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

import re
import sys
import datetime
import contextlib


#----------------------------------------[ assertion functions ]

class NoExceptionRaised(Exception):
    def __init__(self, expected_exception):
        self.expected_exception = expected_exception
    def __str__(self):
        return '%s was expected' % self.expected_exception


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
       :keyword test: Either a function that takes a single argument or a regex.\
                      If `test` is a function, it will be called upon catching the expected exception,\
                      passing the exception instance as argument. A programmer can do\
                      more checks on the specific exception instance in this function, such as check its arguments.\
                      If `test` is a regex in a string, break if str(exception) does not match the regex.

       Specifying test and regex_test are mutually exclusive.

       For example, the following code will execute without letting a test break:
       
       .. code-block:: python
       
          with expected(AssertionError):
              # some code here
              # .....
              # then at some point an exception is raised
              raise AssertionError()
              #.....

       .. versionchanged:: 4.0
          Changed to allow a regex in test keyword argument.
    """

    if test and not callable(test):
        test_regex = test
        def check_message(exc):
            assert re.match(test_regex, str(exc)), \
                'Expected exception to match "%s", got "%s"' % (test_regex, str(exc))
        test = check_message

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


def assert_recent(date, seconds_threshold=5):
    if date is None:
        is_recent_check = False
    else:
        delta = datetime.datetime.now(tz=date.tzinfo) - date
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


