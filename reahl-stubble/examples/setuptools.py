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


#
# Please see the README file for more info.
#

import pkg_resources

from reahl.stubble import EasterEgg


#first we need some stub classes which in real life would be provided
# by another egg as entry points:
class StubClass1:
    pass


class StubClass2:
    pass


#then, we initialise the EasterEgg:
stub_egg = EasterEgg()
pkg_resources.working_set.add(stub_egg)


#then, use 1 of two methods to add the stubbed entry point classes:
group_name = 'xxx'
stub_egg.add_entry_point_from_line(group_name, 'test1 = examples.setuptools:StubClass1')
stub_egg.add_entry_point(group_name, 'test2', StubClass2)

#now, the actual code (which is presumably being tested)
#  (we just print out each class it finds...)
for i in pkg_resources.iter_entry_points(group_name):
    print(i.load())

