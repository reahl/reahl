# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A heading for this module
=========================

Copyright (C) 2009 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

"""
from __future__ import unicode_literals
from __future__ import print_function

from elixir import using_options, Entity, ManyToOne

from reahl.sqlalchemysupport import metadata, Session
from reahl.component.i18n import Translator

_ = Translator('reahl-domain')


class Party(Entity):
    """A Party is any legal entity which the system may keep track of."""
    using_options(metadata=metadata, session=Session, shortnames=True, inheritance='multi')
    system_account = ManyToOne('SystemAccount')



