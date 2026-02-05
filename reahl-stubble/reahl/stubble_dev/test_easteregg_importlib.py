# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys

import pytest

from reahl.stubble.easteregg import ImportlibEasterEgg as EasterEgg, ImportlibEntryPoint

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

PackageNotFoundError = importlib_metadata.PackageNotFoundError
_THIS_MODULE = sys.modules[__name__]

class TestClass2:
    pass


class TestClass1:
    pass


@pytest.fixture
def easter_fixture():
    class EasterFixture:
        group_name = 'abc'
        stub_egg = EasterEgg()

    module_name = __name__
    sys.modules[module_name] = _THIS_MODULE

    try:
        with EasterFixture.stub_egg.installed():
            yield EasterFixture
    finally:
        sys.modules[module_name] = _THIS_MODULE


def test_adding_entry_points_affect_entry_point_map(easter_fixture):
    easter_fixture.stub_egg.add_entry_point_from_line(easter_fixture.group_name,
                      'test1 = reahl.stubble_dev.test_easteregg_importlib:TestClass1')

    easter_fixture.stub_egg.add_entry_point(easter_fixture.group_name, 'test2', TestClass2)

    epmap = easter_fixture.stub_egg.get_entry_map()

    assert list(epmap.keys()) == [easter_fixture.group_name]
    name_to_entry_point = list(epmap.values())[0]
    assert len(list(name_to_entry_point.keys())) == 2

    assert isinstance(name_to_entry_point['test1'], ImportlibEntryPoint)
    assert name_to_entry_point['test1'].load() is TestClass1
    assert isinstance(name_to_entry_point['test2'], ImportlibEntryPoint)
    assert name_to_entry_point['test2'].load() is TestClass2

    easter_fixture.stub_egg.clear()
    assert not easter_fixture.stub_egg.get_entry_map()


def test_entry_points_visible_to_importlib_metadata(easter_fixture):
    easter_fixture.stub_egg.add_entry_point_from_line(
        easter_fixture.group_name,
        'test1 = reahl.stubble_dev.test_easteregg_importlib:TestClass1')

    easter_fixture.stub_egg.add_entry_point(
        easter_fixture.group_name,
        'test2',
        TestClass2)

    entry_points_from_group_kw = importlib_metadata.entry_points(group=easter_fixture.group_name)
    names_from_group_kw = [entry_point.name for entry_point in entry_points_from_group_kw]
    assert 'test1' in names_from_group_kw
    assert 'test2' in names_from_group_kw

    loaded_targets = {entry_point.name: entry_point.load() for entry_point in entry_points_from_group_kw}
    assert loaded_targets['test1'] is TestClass1
    assert loaded_targets['test2'] is TestClass2

    names_from_all = [
        entry_point.name
        for entry_point in importlib_metadata.entry_points().select(group=easter_fixture.group_name)
    ]
    assert 'test1' in names_from_all
    assert 'test2' in names_from_all


def test_distribution_visible_to_importlib_metadata(easter_fixture):
    distribution = importlib_metadata.distribution(easter_fixture.stub_egg.project_name)
    assert distribution is easter_fixture.stub_egg
    assert distribution.metadata['Name'] == easter_fixture.stub_egg.project_name
    assert distribution.version == easter_fixture.stub_egg.version

    distribution_lower = importlib_metadata.distribution(easter_fixture.stub_egg.project_name.lower())
    assert distribution_lower is easter_fixture.stub_egg


def test_distribution_removed_after_deactivate():
    package_name = 'reahl-easteregg-testpkg'
    egg = EasterEgg(name=package_name)
    with egg.installed():
        pass

    with pytest.raises(PackageNotFoundError):
        importlib_metadata.distribution(package_name)
