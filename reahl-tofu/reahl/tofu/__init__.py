# Copyright 2006, 2009, 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


"""
Tofu started out its life as a complete test framework. Tofu has since
been rewritten as independently usable test utilities, some of which
are integrated to work as a plugin with `nosetests
<http://nose.readthedocs.org>`_.

The defining feature of Tofu is its ability to let you write
a hierarchy of test fixtures that is *completely* decoupled from your
hierarchy of tests or test suites.

Tofu also gobbled up another little test project, called `tut` which
implemented a few utilities for testing exceptions, dealing with
temporary files, etc. All this functionality is now also part of Tofu.
"""
from __future__ import unicode_literals
from __future__ import print_function

from reahl.tofu.fixture import Fixture
from .nosesupport import test
from reahl.tofu.fixture import Scenario as scenario
from reahl.tofu.fixture import SetUp as set_up
from reahl.tofu.fixture import TearDown as tear_down

from .checks import *
from .files import *
