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


from tempfile import NamedTemporaryFile
import os
import pkg_resources

import pytest

from reahl.stubble import EasterEgg


class TestClass2:
    pass

class TestClass1:
    pass

@pytest.fixture
def easter_fixture():
    class EasterFixture:
        group_name = 'abc'
        stub_egg = EasterEgg()

    saved_working_set = pkg_resources.working_set
    pkg_resources.working_set = pkg_resources.WorkingSet()
    pkg_resources.working_set.add(EasterFixture.stub_egg)
    yield EasterFixture
    pkg_resources.working_set = saved_working_set


def test_adding_entry_points_affect_entry_point_map(easter_fixture):
    easter_fixture.stub_egg.add_entry_point_from_line(easter_fixture.group_name,
                      'test1 = reahl.stubble_dev.test_easteregg:TestClass1')

    easter_fixture.stub_egg.add_entry_point(easter_fixture.group_name, 'test2', TestClass2)


    epmap = easter_fixture.stub_egg.get_entry_map()

    assert list(epmap.keys()) == [easter_fixture.group_name]
    name_to_entry_point = list(epmap.values())[0]
    assert len(list(name_to_entry_point.keys())) == 2

    assert isinstance(name_to_entry_point['test1'], pkg_resources.EntryPoint)
    assert name_to_entry_point['test1'].load() is TestClass1
    assert isinstance(name_to_entry_point['test2'], pkg_resources.EntryPoint)
    assert name_to_entry_point['test2'].load() is TestClass2


    easter_fixture.stub_egg.clear()
    assert not easter_fixture.stub_egg.get_entry_map()


def test_resource_api(easter_fixture):
    test_file = NamedTemporaryFile(mode='wb+')
    dirname, file_name = os.path.split(test_file.name)

    easter_fixture.stub_egg.location = dirname
    easter_fixture.stub_egg.activate()

    assert pkg_resources.resource_exists(easter_fixture.stub_egg.as_requirement(), file_name)
    assert not pkg_resources.resource_exists(easter_fixture.stub_egg.as_requirement(), 'IDoNotExist')

    contents = b'asdd '
    test_file.write(contents)
    test_file.flush()

    as_string = pkg_resources.resource_string(easter_fixture.stub_egg.as_requirement(), file_name)
    assert as_string == contents

    as_file = pkg_resources.resource_stream(easter_fixture.stub_egg.as_requirement(), file_name)
    assert as_file.read() == contents


def test_resource_api_from_module_name(easter_fixture):
    test_file = NamedTemporaryFile(mode='wb+', suffix='.py')
    dirname, file_name = os.path.split(test_file.name)

    easter_fixture.stub_egg.location = dirname
    easter_fixture.stub_egg.activate()

    module_name = file_name.split('.')[0]
    assert pkg_resources.resource_exists(module_name, '')
    assert pkg_resources.resource_filename(module_name, '') == dirname
