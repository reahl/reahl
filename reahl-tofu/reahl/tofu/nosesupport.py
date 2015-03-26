# Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import re
import os
import six
import logging

try:
    from nose.tools import make_decorator
    from nose.plugins import Plugin
except ImportException:
    msg = 'nose not available, nosesupport disabled'
    logging.warn(msg)
    def make_decorator(f):
        raise AssertionError(msg)
    class Plugin(object):
        def __init__(self, *args, **kwargs):
            raise AssertionError(msg)

# Copied from reahl-component (in order to prevent reahl-tofu to be dependent in reahl-component)
#  (was) from reahl.component.py3compat import ascii_as_bytes_or_str
def ascii_as_bytes_or_str(unicode_str):
    if six.PY2:
        return unicode_str.encode('ascii')
    else:
        return unicode_str


run_fixture = None

def set_run_fixture(fixture, namespace):
    """Adds setup and teardown methods to the calling context that will set a fixture
       as the run fixture for tests in that context.

       The run fixture is set up only once: before any tests are run in the calling context, 
       and torn down once after all tests in this context have run. Fixtures used by tests
       in this context will have their `.run_fixture` set to the Fixture instance you
       set here.

       :arg fixture: The Fixture instance to use as run fixture for this context.
       :arg namespace: Pass `locals()` from the context where set_run_fixture is called here.

       .. versionadded:: 3.1
    """
    def setup():
        global run_fixture
        fixture.__enter__()
        run_fixture = fixture

    def teardown(self):
        global run_fixture
        fixture.__exit__(None, None, None)
        run_fixture = None

    namespace['setup'] = setup
    namespace['teardown'] = teardown


class IsTestWithFixture(object):
    """Use as decorator to mark a method or function as being a test that nose should run. The given Fixture
       class will be instantiated and setup before the test is run, and passed to to the method as its single
       argument.

       For example:

       .. code-block:: python
       
          class MyFixture(Fixture):
              def new_something(self):
                  return 'something'

          @test(MyFixture)
          def some_function(self, fixture):
              assert fixture.something == 'something'
    """
    def __init__(self, fixture_class):
        self.fixture_class = fixture_class

    @property
    def run_fixture(self):
        return run_fixture

    def __call__(self, func):
        @make_decorator(func)
        def with_fixture(*args):
            fixture = args[-1]
            with fixture:
                with fixture.context:
                    return func(*args)

        @make_decorator(func)
        def scenario_generator(*args):
            for scenario in self.fixture_class.get_scenarios():
                fixture = self.fixture_class.for_scenario(run_fixture, scenario)
                yield (with_fixture,)+args+(fixture,)
        scenario_generator.__test__ = True
        return scenario_generator

test = IsTestWithFixture

def import_string_spec(string_spec):
    bits = string_spec.split(':')
    assert len(bits) == 2
    [module_name, class_name] = bits

    module = __import__(module_name, [class_name])
    attr_names = module_name.split('.')[1:]+[class_name]
    current = module
    for attr in attr_names:
        if not hasattr(current, attr):
            raise AssertionError('The locator "%s" is not valid: cannot find %s in %s' % (string_spec, attr, current))
        current = getattr(current, attr)
    return current


class RunFixturePlugin(Plugin):
    """A plugin for nose which creates and sets up a run fixture during the test run. Enable this plugin
       by passing ``--with-run-fixture=<locator>`` to nosetests on the commandline.

       ``<locator>`` is a string specifying how to find a Fixture class. It starts with the name of the
       Python package where the class is defined, followed by a colon and then the name of the class.
       For example: "reahl.webdev.fixtures:WebFixture"
    """
    name = ascii_as_bytes_or_str('run-fixture')

    def options(self, parser, env=os.environ):
        parser.add_option(ascii_as_bytes_or_str("-F"), ascii_as_bytes_or_str("--with-run-fixture"),
                          action="store", dest="run_fixture", default=None,
                          help="the run fixture to use")


    def configure(self, options, conf):
        super(RunFixturePlugin, self).configure(options, conf)
        if options.run_fixture:
            self.enabled = True
        if not self.enabled:
            return

        run_fixture_class = import_string_spec(options.run_fixture)
        self.run_fixture  = run_fixture_class(None)
        self.run_fixture.__enter__()
        global run_fixture
        run_fixture = self.run_fixture

    def finalize(self, result):
        exception_type, value, traceback = None, None, None
        self.run_fixture.__exit__(exception_type, value, traceback)
        global run_fixture
        run_fixture = None


class LongOutputPlugin(Plugin):
    """A plugin for nose which lets nose output the name of each test before it starts running it.
       Enable this plugin by passing ``--with-long-output`` to nosetests on the commandline.
    """
    name = ascii_as_bytes_or_str('long-output')
    def setOutputStream(self, stream):
        self.output = stream

    def startTest(self, test):
        print('%s [' % test, file=self.output)

    def stopTest(self, test):
        print('] done.', file=self.output)


class TestDirectoryPlugin(Plugin):
    """A plugin for nose which changes how nose finds tests to run. It lets you specify a test directory
       and will search all modules (recursively) inside that test directory only. Each python file is
       searched, and anything marked with an @test or nose's @istest is run as a test.

       Enable this plugin by passing ``--with-test-directory=<directory path relative to current dir>`` to nosetests on the commandline.
    """
    name = ascii_as_bytes_or_str('test-directory')
    def options(self, parser, env=os.environ):
        parser.add_option(ascii_as_bytes_or_str("-T"), ascii_as_bytes_or_str("--with-test-directory"),
                          action="store", dest="test_directory", default="",
                          help="the directories (relative to the current directory) to search for tests (can be a regex)")

    def configure(self, options, conf):
        super(TestDirectoryPlugin, self).configure(options, conf)
        if options.test_directory:
            self.enabled = True

        if self.enabled:
            self.test_directory_regex = options.test_directory

    def wantDirectory(self, dirname):
        return dirname.startswith(os.getcwd())

    def wantFile(self, file_):
        rel_file = os.path.relpath(file_)
        return re.match('%s.*\.py$' % self.test_directory_regex, rel_file) is not None

    def wantModule(self, module):
        module_directory = os.path.dirname(module.__file__)
        return module_directory.startswith(os.getcwd())
        
    def wantClass(self, cls):
        return getattr(cls, '__test__', False)

    def wantMethod(self, method):
        return getattr(method, '__test__', False)

    def wantFunction(self, function):
        return getattr(function, '__test__', False)


class LogLevelPlugin(Plugin):
    """A plugin for nose which sets the log level for the test run.

       Enable this plugin by passing ``--with-log-level=(ERROR|WARNING|INFO|DEBUG)`` to nosetests on the commandline.
    """
    name = ascii_as_bytes_or_str('log-level')
    def options(self, parser, env=os.environ):
        parser.add_option(ascii_as_bytes_or_str("-L"), ascii_as_bytes_or_str("--with-log-level"),
                          action="store", dest="log_level", default='WARNING',
                          help="the log level at which to emit log statements")

    def configure(self, options, conf):
        super(LogLevelPlugin, self).configure(options, conf)
        self.enabled = True
        logging.getLogger('').setLevel(options.log_level.upper())


class SetUpFixturePlugin(Plugin):
    """A plugin for nose which only runs the setup of a given Fixture, no tests, and no tear down. This is
       useful for creating a demo database with useful contents.

       Enable this plugin by passing ``--with-setup-fixture=<locator>`` to nosetests on the commandline.

       ``<locator>`` is a string specifying how to find a Fixture class. It starts with the name of the
       Python package where the class is defined, followed by a colon and then the name of the class.
       For example: "reahl.webdev.fixtures:WebFixture"
    """
    name = ascii_as_bytes_or_str('setup-fixture')

    def options(self, parser, env=os.environ):
        parser.add_option(ascii_as_bytes_or_str("--with-setup-fixture"),
                          action="store", dest="setup_fixture", default=None,
                          help="just run the set_up and tear_down of this fixture")


    def configure(self, options, conf):
        super(SetUpFixturePlugin, self).configure(options, conf)
        if options.setup_fixture:
            self.enabled = True
            self.setup_fixture_class = import_string_spec(options.setup_fixture)

    def begin(self):
        self.setup_fixture  = self.setup_fixture_class(run_fixture)
        self.setup_fixture.__enter__()

    def finalize(self, result):
        exception_type, value, traceback = None, None, None
        self.setup_fixture.__exit__(exception_type, value, traceback)

    def wantDirectory(self, dirname):
        return False

    def report(self, stream):
        print('Finished running %s' % self.setup_fixture, file=stream)
        return True
        
  
from nose.plugins.attrib import AttributeSelector
from nose.selector import Selector
import unittest
log = logging.getLogger(__name__)
class MarkedTestsSelector(Selector):
    def wantClass(self, cls):
        is_test = getattr(cls, '__test__', False) or issubclass(cls, unittest.TestCase)
        wanted = is_test and not (self.plugins.wantClass(cls) is False)
        log.debug("wantClass %s? %s", cls, wanted)
        return wanted

    def wantFunction(self, function):
        if not hasattr(function, '__name__'):
            return False
        is_test = getattr(function, '__test__', False)
        wanted = is_test and not (self.plugins.wantFunction(function) is False)
        log.debug("wantFunction %s? %s", function, wanted)
        return wanted

    def wantMethod(self, method):
        if not hasattr(method, '__name__'):
            return False
        is_test = getattr(method, '__test__', False)
        wanted = is_test and not (self.plugins.wantMethod(method) is False)
        log.debug("wantMethod %s? %s", method, wanted)
        return wanted

    def wantModule(self, module):
        is_test = getattr(module, '__test__', True)
        wanted = is_test and not (self.plugins.wantModule(module) is False)
        return wanted


class MarkedTestsPlugin(Plugin):
    """A Nose plugin that changes the meaning of testMatch, include and exclude patterns. With --marked-tests,
       thse patterns are only applied to file and directory names, and disregarded when modules and the Python
       objects inside them are assessed.

       Python objects are regarded as tests only of they are marked marked with an @test or nose's @istest.
       Python modules are regarded as test modules regardless of name except if __test__ is explicitly set
       to False in the __init__.py of that module.

       Enable this plugin by passing ``--with-marked-tests`` to nosetests on the commandline.

       .. versionadded:: 3.1
    """
    name = ascii_as_bytes_or_str('marked-tests')
    def options(self, parser, env=os.environ):
        parser.add_option(ascii_as_bytes_or_str("-t"), ascii_as_bytes_or_str("--with-marked-tests"),
                          action="store_true", dest="marked_tests", default=False,
                          help="apply naming conventions to files and directories only, Python artifacts are tests when explicitly marked with @istest")

    def configure(self, options, conf):
        super(MarkedTestsPlugin, self).configure(options, conf)
        if options.marked_tests:
            self.enabled = True

    def prepareTestLoader(self, loader):
        if self.enabled:
            loader.selector = MarkedTestsSelector(loader.config)

#    def describeTest(self, test):
#        return str(test)


