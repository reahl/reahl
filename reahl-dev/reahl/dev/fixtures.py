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

# Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)



import sys
import copy
import pkg_resources
import contextlib

try:
  from setuptools.config.setupcfg import read_configuration
except ImportError:
  from setuptools.config import read_configuration

from reahl.tofu import Fixture, set_up, tear_down, scope, uses
from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.config import StoredConfiguration, ReahlSystemConfig
from reahl.component.shelltools import Executable
from reahl.dev.exceptions import CouldNotConfigureServer
from reahl.tofu.pytestsupport import WithFixtureDecorator
from reahl.stubble import stubclass, exempt, replaced


class ContextAwareFixture(Fixture):
    """A ContextAwareFixture is a :class:`~reahl.tofu.Fixture` which has
    an :class:`~reahl.component.context.ExecutionContext` as one of its
    elements.

    Such a Fixture ensures that its setup and teardown actions are
    done within its `.context`, and that tests using it are also run
    within its `.context`.

    """
    def new_context(self):
        raise ProgrammerError('No ExecutionContext defined for %s. You must override new_context() or set an attribute or @property named "context"' % self)

    def __enter__(self):
        #TODO: need tp replace this by calling context.__enter_ explicitly once stop= is removed
        self.context.install_with_context_vars_or_frames(stop=lambda f: isinstance(f.f_locals.get('self', None), WithFixtureDecorator))
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        suppress_exception = [self.context.__exit__(exc_type, exc_val, exc_tb),
                              super().__exit__(exc_type, exc_val, exc_tb)]
        return any(suppress_exception)

    def run_tear_down_actions(self):
        with self.context:
            return super().run_tear_down_actions()


@scope('session')
class ReahlSystemSessionFixture(ContextAwareFixture):
    """A session-scoped :class:`~reahl.tofu.Fixture` which sets up all the basics any Reahl system needs to run.

    Upon set up, it creates a new empty database with the correct
    database schema for the project and sets up any persistent classes
    for use with that schema. It also connects to the database. Upon
    tear down, the Fixture disconnects from the database.

    To be able to do all that, it needs to provide a basic
    :class:`~reahl.component.context.ExecutionContext` with the
    appropriate configuration, which it reads from the 'etc' directory
    relative to the current directory.

    .. note::

       You should not use this fixture directly in tests because
       changes to, eg. the
       :class:`~reahl.component.context.ExecutionContext` it provides
       will persist between different tests. The idea is for
       ReahlSystemSessionFixture to be used by other
       :class:`~reahl.tofu.Fixture`\s that are not session scoped, but
       that uses this one where necessary. See for example
       :class:`ReahlSystemFixture`.

    """
    commit = False

    def new_reahlsystem(self):
        return self.config.reahlsystem

    def new_config(self):
        """The main :class:`~reahl.component.config.Configuration` of the system.

        This is read from disk from the 'etc' directory present in the current working directory where tests are run.
        """
        config = StoredConfiguration('etc/')
        try:
            config.configure(include_test_dependencies=self.test_dependencies)
        except pkg_resources.DistributionNotFound as ex:
            raise CouldNotConfigureServer(ex).with_traceback(sys.exc_info()[2])

        return config

    def new_context(self, config=None, system_control=None):
        """The :class:`~reahl.component.context.ExecutionContext` within which all tests are run."""
        with ExecutionContext(name=self.__class__.__name__) as context:
            context.config = config or self.config
            context.system_control = system_control or self.system_control
        return context

    def new_system_control(self):
        """The :class:`~reahl.component.dbutils.SystemControl` with which you can control the underlying database. """
        return SystemControl(self.config)

    def new_test_dependencies(self):
        try:
            return read_configuration('setup.cfg')['options']['tests_require']
        except KeyError:
            return []

    @set_up
    def init_database(self):
        orm_control = self.config.reahlsystem.orm_control
        for dependency in self.test_dependencies:
            orm_control.instrument_classes_for(dependency)
        if not self.system_control.is_in_memory:
            self.system_control.initialise_database()
        self.system_control.connect()

    @tear_down
    def disconnect(self):
        if self.system_control.connected:
            self.system_control.disconnect()

    
    
@uses(reahl_system_fixture=ReahlSystemSessionFixture)
class ReahlSystemFixture(ContextAwareFixture):
    """A :class:`~reahl.tofu.Fixture` for direct use in test which sets up all the basics any Reahl system needs to run.

    ReahlSystemFixture does its work by using a
    :class:`ReahlSystemSessionFixture` behind the
    scenes. ReahlSystemFixture provides copies of most of the
    session-scoped stuff in the
    :class:`ReahlSystemSessionFixture`. This allows you to "inherit"
    the configuration set up for the session by default, but also
    allows you to change the configuration and ExecutionContext for a
    particular test, safe in the knowledge that such changes will be
    torn down after each test function ran.

    """
    @property
    def system_control(self):
        return self.reahl_system_fixture.system_control

    @set_up
    def ensure_connected(self): # In case a test nuked the connection
        if not self.system_control.connected:
            self.system_control.connect()

    def new_context(self, config=None, session=None):
        context = ExecutionContext(parent_context=self.reahl_system_fixture.context)
        context.config = config or self.config
        context.system_control = self.system_control
        return context

    def new_config(self, reahlsystem=None):
        config = copy.copy(self.reahl_system_fixture.config)
        config.reahlsystem = reahlsystem or self.reahlsystem
        return config

    def new_reahlsystem(self, root_egg=None, connection_uri=None, orm_control=None):
        reahlsystem = ReahlSystemConfig()
        reahlsystem.root_egg = root_egg or self.reahl_system_fixture.reahlsystem.root_egg
        reahlsystem.connection_uri = connection_uri or self.reahl_system_fixture.reahlsystem.connection_uri
        reahlsystem.orm_control = orm_control or self.reahl_system_fixture.reahlsystem.orm_control
        reahlsystem.debug = True
        return reahlsystem
            

    
class MonitoredInvocation:
    def __init__(self, method, commandline_arguments, args, kwargs):
        self.method = method
        self.commandline_arguments = commandline_arguments
        self.args = args
        self.kwargs = kwargs

    @property
    def argv(self):
        return self.commandline_arguments


@stubclass(Executable)
class ExecutableStub(Executable):
    def __init__(self, name='fake executable', stdout=''):
        super().__init__(name)
        self.calls = []
        self.stdout = stdout

    def __repr__(self):
        return 'StubExecutable(\'%s\')' % self.name
    
    @exempt
    @property
    def times_called(self):
        return len(self.calls)

    def execute(self, method, commandline_arguments, *args, **kwargs):
        self.calls.append(MonitoredInvocation(method, commandline_arguments, args, kwargs))
        if self.stdout:
            out = kwargs.get('stdout', sys.stdout)
            print(self.stdout, file=out)

    @exempt
    @contextlib.contextmanager
    def inserted_as_shim(self):
        executable = self
        saved_which = Executable.which
        def stub_which(self, program):
            full_path_to_executable = saved_which(self, program)
            if program in [full_path_to_executable, executable.name]:
                return program
            else:
                return full_path_to_executable

        saved_execute = Executable.execute
        def stub_execute(self, method, commandline_arguments, *args, **kwargs):
            if executable.name == self.name:
                return executable.execute(method, commandline_arguments, *args, **kwargs)
            else:
                return saved_execute(self, method, commandline_arguments, *args, **kwargs)

        stub_which.__name__ = 'which'
        stub_execute.__name__ = 'execute'
        with replaced(Executable.which, stub_which, Executable), replaced(Executable.execute, stub_execute, Executable):
            yield executable
    
