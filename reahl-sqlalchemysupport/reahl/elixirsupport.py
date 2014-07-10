# Copyright 2010, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from elixir import ManyToOne

from reahl.component.context import ExecutionContext

def session_scoped(cls):
    cls.session = ManyToOne('UserSession', ondelete='cascade')
    @classmethod
    def for_current_session(cls, **kwargs):
        session = ExecutionContext.get_context().session
        found = cls.query.filter_by(session=session)
        if found.count() >= 1:
            return found.one()
        return cls(session=session, **kwargs)
    cls.for_current_session = for_current_session

    return cls

