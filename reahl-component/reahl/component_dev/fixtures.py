# Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.exceptions import ProgrammerError
from reahl.tofu.pytestsupport import WithFixtureDecorator
from reahl.tofu import Fixture


class ContextAwareFixture(Fixture):
    def new_context(self):
        raise ProgrammerError('No ExecutionContext defined for %s. You must override new_context() or set an attribute or @property named "context"' % self)

    def __enter__(self):
        self.context.install(lambda f: isinstance(f.f_locals['self'], WithFixtureDecorator))
        return super(ContextAwareFixture, self).__enter__()

    def run_tear_down_actions(self):
        self.context.install()
        return super(ContextAwareFixture, self).run_tear_down_actions()

