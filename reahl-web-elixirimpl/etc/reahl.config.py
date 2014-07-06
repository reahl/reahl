# Copyright 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

TODO: This should be a short paragraph explaining what's in this module.
If this file is the __init__.py of some package, it should be a
description of the package.

""" 
from __future__ import unicode_literals
from __future__ import print_function

import os
import os.path

from reahl.sqlalchemysupport import SqlAlchemyControl

eggName = os.path.basename(os.getcwd())
reahlsystem.root_egg = eggName
reahlsystem.connection_uri = 'postgresql://rhug:rhug@localhost/rhug'
#reahlsystem.connection_uri = 'sqlite://'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)



