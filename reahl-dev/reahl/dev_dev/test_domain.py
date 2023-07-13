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



import os
import os.path
import filecmp

import pytest

from reahl.tofu import temp_dir, temp_file_with, expected, Fixture
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import exempt
from reahl.stubble import stubclass

from reahl.dev.devdomain import DebianPackage, SshRepository, LocalAptRepository, RepositoryLocalState, Workspace, \
    ProjectMetadata, Project, SubstvarsFile, \
    Dependency, ThirdpartyDependency, DebianChangelog, DebianControl, VersionNumber
from reahl.dev.exceptions import AlreadyUploadedException, NotBuiltException, NotAValidProjectException, \
    InvalidProjectFileException


class RepositoryUploadFixture(Fixture):
    def new_incoming_directory(self):
        return temp_dir()
    def new_to_upload_directory(self):
        return temp_dir()
    def new_state_directory(self):
        return temp_dir()

    def new_to_upload_file1(self):
        return self.to_upload_directory.file_with('piet.changes', 'kerneels')
    def new_to_upload_file2(self):
        return self.to_upload_directory.file_with('piet.deb', 'black cat')

    def new_package(self):
        fixture = self
        @stubclass(DebianPackage)
        class PackageStub:
            _built = False
            unique_id = 'therecanonlybeone'
            @property
            def is_built(self):
                return self._built

            @property
            def files_to_distribute(self):
                return [fixture.to_upload_file1.name, fixture.to_upload_file2.name]

            def build(self, sign=True):
                self._built = True

        return PackageStub()

    def new_workspace(self):
        fixture = self
        @stubclass(Workspace)
        class WorkspaceStub:
            repository_state_directory = fixture.state_directory.name

        return WorkspaceStub()

    def new_debian_repository(self):
        user = os.environ.get('USER', None)
        return SshRepository(self.workspace, 'localhost', user, self.incoming_directory.name)


@with_fixtures(RepositoryUploadFixture)
def test_upload_not_built(repository_upload_fixture):
    fixture = repository_upload_fixture
    # Case where you upload something that's not been built yet
    assert not fixture.debian_repository.is_uploaded(fixture.package)
    assert not fixture.package.is_built
    with expected(NotBuiltException):
        fixture.debian_repository.upload(fixture.package, [])


@with_fixtures(RepositoryUploadFixture)
def test_upload_success(repository_upload_fixture):
    fixture = repository_upload_fixture
    fixture.package.build()

    # Case where it works
    assert not fixture.debian_repository.is_uploaded(fixture.package)
    assert fixture.package.is_built

    fixture.debian_repository.upload(fixture.package, [])
    assert fixture.debian_repository.is_uploaded(fixture.package)
    assert fixture.package.files_to_distribute
    for filename in fixture.package.files_to_distribute:
        filename_only = os.path.basename(filename)
        incoming_filename = os.path.join(fixture.incoming_directory.name, filename_only)
        assert filecmp.cmp(filename, incoming_filename)

    # Case where you try upload something again
    assert fixture.debian_repository.is_uploaded(fixture.package)
    assert fixture.package.is_built
    with expected(AlreadyUploadedException):
        fixture.debian_repository.upload(fixture.package, [])


def test_reading_and_writing_repository():
    repository_state_dir = temp_dir()
    @stubclass(SshRepository)
    class RepositoryStub:
        @property
        def unique_id(self):
            return 'myid'

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


def test_queries():
    @stubclass(DebianPackage)
    class PackageStub:
        def __init__(self, name):
            self.name = name

        @property
        def unique_id(self):
            return self.name

    package1 = PackageStub('myname')
    package2 = PackageStub('yourname')


    @stubclass(SshRepository)
    class RepositoryStub:
        pass

    repository = RepositoryStub()
    local_state = RepositoryLocalState(repository)

    local_state.set_uploaded(package1)

    assert local_state.is_uploaded(package1)
    assert not local_state.is_uploaded(package2)



@stubclass(DebianPackage)
class DebianPackageStub:
    package_files = ['equivs-dummy_1.0_all.deb',  'equivs-dummy_1.0.dsc',
                     'equivs-dummy_1.0_i386.changes', 'equivs-dummy_1.0.tar.gz']
    def __init__(self):
        self.temp_directory = temp_dir()
        self.create_files()

    @exempt
    def create_files(self):
        self.file1 = self.temp_directory.file_with(self.package_files[0], 'aaa')
        self.file2 = self.temp_directory.file_with(self.package_files[1], 'bbb')
        self.file3 = self.temp_directory.file_with(self.package_files[2], 'bbb')
        self.file4 = self.temp_directory.file_with(self.package_files[3], 'bbb')

    @property
    def build_output_files(self):
        return [self.file1.name, self.file2.name, self.file3.name, self.file4.name]


class DebianPackageStubWithRealFiles(DebianPackageStub):
    @property
    def build_output_files(self):
        return [os.path.join(self.temp_directory.name, filename) for filename in self.package_files]

    @exempt
    def create_files(self):
        control_file_contents = """Section: misc
Priority: optional
Standards-Version: 8.0.0

Package: equivs-dummy
Version: 1.0
Maintainer: %s <%s>
Architecture: all
Description: some wise words
 long description and info
 .
 second paragraph

""" % (os.environ['DEBFULLNAME'], os.environ['DEBEMAIL'])
        self.temp_directory.file_with('control', control_file_contents)
        for f in self.build_output_files:
            with open(f, 'a'):
                os.utime(f, None)


class LocalAptRepositoryFixture(Fixture):
    def new_repository_directory(self):
        return temp_dir()

    def new_repository(self):
        return LocalAptRepository(os.path.join(self.repository_directory.name, 'repo'))

    def new_package(self):
        return DebianPackageStub()


@with_fixtures(LocalAptRepositoryFixture)
def test_creation_of_directory(local_apt_repository_fixture):
    fixture = local_apt_repository_fixture
    package = fixture.package
    repository = fixture.repository

    # Case: when a repository is made the first time, it creates its root_directory
    assert os.path.isdir(repository.root_directory)
    repository.upload(package, [])
    assert repository.is_uploaded(package)

    # Case: when a repository is made a second time, it preserves the underlying directory
    repository2 = LocalAptRepository(repository.root_directory)
    assert repository.is_uploaded(package)
    assert repository2.is_uploaded(package)


@with_fixtures(LocalAptRepositoryFixture)
def test_uploading(local_apt_repository_fixture):
    fixture = local_apt_repository_fixture
    package = fixture.package
    repository = fixture.repository

    # Case: uploading files
    assert not repository.is_uploaded(package)
    repository.upload(package, [])
    assert repository.is_uploaded(package)
    assert package.package_files

    for filename in package.package_files:
        assert os.path.isfile(os.path.join(repository.root_directory, filename))

    # Case: removing uploaded
    repository.remove_uploaded(package)
    for filename in repository.uploaded_files_for(package):
        assert not os.path.isfile(filename)


@with_fixtures(LocalAptRepositoryFixture)
def test_index_building(local_apt_repository_fixture):
    fixture = local_apt_repository_fixture
    package = DebianPackageStubWithRealFiles()
    repository = fixture.repository
    repository.upload(package, [])

    repository.build_index_files()
    repository.sign_index_files(default_key='23203326628B5A6925BFB3EC37019E3ADE633F86')
    for filename in ['Packages','Release','Release.gpg']:
        assert os.path.isfile( os.path.join(repository.root_directory, filename))




# -- Tests for manipulating debian substvar files.
def test_reading_and_writing_substvar_files():
    raw_file = temp_file_with('')
    substvars = SubstvarsFile(raw_file.name)
    substvars.extend( [('python:Version', 'python stuff'), ('reahl:Depends', 'lots of depends')] )

    substvars.write()

    substvars = SubstvarsFile(raw_file.name)
    assert len(substvars) == 0
    substvars.read()

    assert len(substvars) == 2
    assert list(substvars.items())[0] == ('python:Version', 'python stuff')
    assert list(substvars.items())[1] == ('reahl:Depends', 'lots of depends')


def test_dict_interface():
    substvars = SubstvarsFile(None)
    substvars.extend( [('python:Version', 'python stuff'), ('reahl:Depends', 'lots of depends')] )

    assert substvars['python:Version'] == 'python stuff'
    assert substvars['reahl:Depends'] == 'lots of depends'

    substvars['python:Version'] = 'other stuff'
    assert substvars['python:Version'] == 'other stuff'

    substvars['reahl:Goods'] = 'more goods'
    assert substvars['reahl:Goods'] == 'more goods'

    assert len(substvars) == 3
    assert list(substvars.items())[0] == ('python:Version', 'other stuff')
    assert list(substvars.items())[1] == ('reahl:Depends', 'lots of depends')
    assert list(substvars.items())[2] == ('reahl:Goods', 'more goods')




# -- Tests regarding the debian changelog file
@pytest.fixture
def changelog_file():
        changlog_file = temp_file_with('''
python-reahl (2.0.0a1) unstable; urgency=low

  * Towards version 2.0.

 -- Iwan Vosloo <iwan@reahl.org>  Tue, 08 Feb 2011 12:03:44 +0000

python-reahl (0.8.0) unstable; urgency=low

  * Initial Release.

 -- Iwan Vosloo <iwan@reahl.org>  Wed, 22 Dec 2010 05:44:11 +0000
''')
        yield changlog_file


def test_parsing_changelog_name(changelog_file):
    changelog = DebianChangelog(changelog_file.name)
    assert changelog.package_name == 'python-reahl'


def test_parsing_changelog_version(changelog_file):
    changelog = DebianChangelog(changelog_file.name)
    assert changelog.version == '2.0.0a1'



@pytest.fixture
def control_file():
    control_file = temp_file_with('''
Source: python-reahl
Section: reahl
Priority: optional
Maintainer: Reahl Software Services <info@reahl.org>
Build-Depends: debhelper (>= 7), python-support (>= 1.0), python (>= 2.6), python (<< 3.0)
Standards-Version: 3.8.3

Package: python-reahl-component
Architecture: all
Depends: python-setuptools, ${python:Depends}, ${reahl:Depends}
Provides: ${python:Provides}
Description: Reahl-component.
Reahl-component - long description.

Package: python-reahl-stubble
Architecture: all
Depends: ${python:Depends}, ${reahl:Depends}
Provides: ${python:Provides}
Description: Stub tools for use in unit testing
 one line of description
 another line of description

''' )
    return control_file


def test_debian_control_descriptions(control_file):
    control = DebianControl(control_file.name)

    assert control.get_short_description_for('python-reahl-stubble') == 'Stub tools for use in unit testing'
    expected_long = 'one line of description another line of description '

    assert control.get_long_description_for('python-reahl-stubble') == expected_long

    assert control.get_short_description_for('python-reahl-component') == 'Reahl-component.'


def test_debian_maintainer_info(control_file):
    control = DebianControl(control_file.name)

    assert control.maintainer_name == 'Reahl Software Services'
    assert control.maintainer_email == 'info@reahl.org'


