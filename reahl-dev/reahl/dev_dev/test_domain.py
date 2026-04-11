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



import os
import os.path

from reahl.tofu import Fixture, scenario, temp_dir
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import stubclass

from reahl.dev.devdomain import PackageIndex, PythonSourcePackage, PythonWheelPackage, RepositoryLocalState


def test_reading_and_writing_repository():
    repository_state_dir = temp_dir()
    @stubclass(PackageIndex)
    class RepositoryStub:
        @property
        def unique_id(self):
            return 'myid'

        def transfer(self, package):
            pass

        repository_state_directory = repository_state_dir.name

    repository = RepositoryStub()
    expected_repository_state_file = os.path.join(repository_state_dir.name, '%s.uploaded' % repository.unique_id)

    local_state = RepositoryLocalState(repository)

    # Case: on first read, does not break if file does not exist
    assert not os.path.exists(expected_repository_state_file)
    local_state.read()
    assert local_state.uploaded_project_ids == set([])

    # Case: on write, creates file
    assert not os.path.exists(expected_repository_state_file)
    local_state.uploaded_project_ids = {'someid1', 'someid2'}
    local_state.write()
    assert os.path.isfile(expected_repository_state_file)

    # Case: read existing stuff correctly
    local_state.uploaded_project_ids = set([])
    local_state.read()
    assert local_state.uploaded_project_ids == {'someid1', 'someid2'}


class PackageFilenameFixture(Fixture):
    def new_package(self):
        return self.package_class(self.project)

    def new_project(self):
        class ProjectStub:
            project_name = 'reahl-tofu'
            project_name_pythonised = 'reahl_tofu'
            distribution_name = 'reahl_tofu'
            version = '7.0.4'
            workspace = None

        return ProjectStub()


class PackageFilenameScenarios(Fixture):
    @scenario
    def source_distribution(self):
        """AI: Source distribution filenames follow the build backend's normalised distribution name."""
        self.package_class = PythonSourcePackage
        self.expected_filename = 'reahl_tofu-7.0.4.tar.gz'

    @scenario
    def wheel_distribution(self):
        """AI: Wheel filenames follow the normalised distribution name used for built artifacts."""
        self.package_class = PythonWheelPackage
        self.expected_filename = 'reahl_tofu-7.0.4-py3-none-any.whl'


@with_fixtures(PackageFilenameFixture, PackageFilenameScenarios)
def test_distribution_package_filenames_use_normalised_distribution_name(fixture, scenario):
    """Hyphenated project names are normalised to the filenames emitted by the build backend."""
    fixture.package_class = scenario.package_class
    assert fixture.package.package_files == [scenario.expected_filename]
