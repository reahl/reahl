# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

import six
import sys
import copy
import pkg_resources

from reahl.tofu import Fixture, set_up, tear_down, scope, uses
from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.config import StoredConfiguration, ReahlSystemConfig
from reahl.dev.exceptions import CouldNotConfigureServer
from reahl.tofu.pytestsupport import WithFixtureDecorator

from reahl.tofu import Fixture


class ContextAwareFixture(Fixture):
    def new_context(self):
        raise ProgrammerError('No ExecutionContext defined for %s. You must override new_context() or set an attribute or @property named "context"' % self)

    def __enter__(self):
        self.context.install(lambda f: isinstance(f.f_locals.get('self', None), WithFixtureDecorator))
        return super(ContextAwareFixture, self).__enter__()

    def run_tear_down_actions(self):
        self.context.install()
        return super(ContextAwareFixture, self).run_tear_down_actions()


@scope('session')
class ReahlSystemSessionFixture(ContextAwareFixture):
    """A Fixture to be used as run fixture. Upon set up, it creates a new empty database with the
       correct database schema for the project and sets up any persistent classes for use with that
       schema. It also connects to the database. Upon tear down, the Fixture disconnects from the database.
    """
    commit = False

    def new_reahlsystem(self):
        return self.config.reahlsystem

    def new_config(self):
        config = StoredConfiguration('etc/')
        try:
            config.configure()
        except pkg_resources.DistributionNotFound as ex:
            six.reraise(CouldNotConfigureServer, CouldNotConfigureServer(ex), sys.exc_info()[2])

        return config

    def new_context(self, config=None, system_control=None):
        context = ExecutionContext(name=self.__class__.__name__).install()
        context.config = config or self.config
        context.system_control = system_control or self.system_control
        return context

    def new_system_control(self):
        return SystemControl(self.config)

    def new_test_dependencies(self):
        return []

    @set_up
    def init_database(self):
        orm_control = self.config.reahlsystem.orm_control
        for dependency in self.test_dependencies:
            orm_control.instrument_classes_for(dependency)
        if not self.system_control.is_in_memory:
            self.system_control.initialise_database(yes=True)
        self.system_control.connect()

    @tear_down
    def disconnect(self):
        if self.system_control.connected:
            self.system_control.disconnect()

    
    
@uses(reahl_system_fixture=ReahlSystemSessionFixture)
class ReahlSystemFixture(ContextAwareFixture):
    @property
    def system_control(self):
        return self.reahl_system_fixture.system_control

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
            
