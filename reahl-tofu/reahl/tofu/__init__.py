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


"""Tofu is a collection of test utilities, some of which are
integrated to work as a plugin with `pytest
<http://docs.pytest.org>`_.

The main feature of Tofu is its ability to let you write
of test :py:class:`Fixture` classes, each of which contains a
collection of related objects used in a test.

Tofu also gobbled up another little test project, called `tut` which
implemented a few utilities for testing exceptions, dealing with
temporary files, etc. All this functionality is now also part of Tofu.

"""

from reahl.tofu.fixture import Fixture
from reahl.tofu.fixture import Scenario as scenario
from reahl.tofu.fixture import SetUp as set_up
from reahl.tofu.fixture import TearDown as tear_down
from reahl.tofu.pytestsupport import uses, scope, with_fixtures

from .checks import *
from .files import *
