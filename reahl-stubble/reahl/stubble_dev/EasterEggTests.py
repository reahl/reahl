# Copyright 2006, 2008, 2009, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from tempfile import NamedTemporaryFile
import os
import pkg_resources

from nose.tools import istest

from reahl.stubble import EasterEgg


class TestClass2(object):
    pass


@istest
class EasterEggTests(object):
    class TestClass1(object):
        pass

    def setUp(self):
        self.group_name = 'abc'
        self.stub_egg = EasterEgg()
        self.saved_working_set = pkg_resources.working_set
        pkg_resources.working_set = pkg_resources.WorkingSet()
        pkg_resources.working_set.add(self.stub_egg)

    def tearDown(self):
        pkg_resources.working_set = self.saved_working_set

    @istest
    def test_adding_entry_points_affect_entry_point_map(self):
        self.stub_egg.add_entry_point_from_line(self.group_name,
                          'test1 = reahl.stubble_dev.EasterEggTests:EasterEggTests.TestClass1')

        self.stub_egg.add_entry_point(self.group_name, 'test2', TestClass2)


        epmap = self.stub_egg.get_entry_map()

        assert list(epmap.keys()) == [self.group_name]
        name_to_entry_point = list(epmap.values())[0]
        assert len(list(name_to_entry_point.keys())) == 2

        assert isinstance(name_to_entry_point['test1'], pkg_resources.EntryPoint)
        assert name_to_entry_point['test1'].load() is EasterEggTests.TestClass1
        assert isinstance(name_to_entry_point['test2'], pkg_resources.EntryPoint)
        assert name_to_entry_point['test2'].load() is TestClass2


        self.stub_egg.clear()
        assert not self.stub_egg.get_entry_map()

    @istest
    def test_resource_api(self):
        test_file = NamedTemporaryFile()
        dirname, file_name = os.path.split(test_file.name)

        self.stub_egg.set_module_path(dirname)

        assert pkg_resources.resource_exists(self.stub_egg.as_requirement(), file_name)
        assert not pkg_resources.resource_exists(self.stub_egg.as_requirement(), 'IDoNotExist')

        contents = 'asdd '
        test_file.write(contents)
        test_file.seek(0)

        as_string = pkg_resources.resource_string(self.stub_egg.as_requirement(), file_name)
        assert as_string == contents

        as_file = pkg_resources.resource_stream(self.stub_egg.as_requirement(), file_name)
        assert as_file.read() == contents

