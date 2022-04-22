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
    ProjectMetadata, EggProject, ChickenProject, Project, SubstvarsFile, \
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


# -- Tests for reading Projects from XML files.
def test_generic_project_file_queries():
    workspace_dir = temp_dir()
    project_dir = workspace_dir.temp_dir()
    project_filename = os.path.join(project_dir.name, '.reahlproject')

    @stubclass(Workspace)
    class WorkspaceStub:
        directory = workspace_dir.name
    workspace = WorkspaceStub()

    # Case where the file does not exist
    assert not os.path.exists(project_filename)
    with expected(NotAValidProjectException):
        Project.from_file(workspace, project_dir.name )

    # Case where the file exists, but is empty
    xml_file = project_dir.file_with('.reahlproject', '')
    with expected(InvalidProjectFileException):
        Project.from_file(workspace, project_dir.name)

    # Case where the file exists with stuff in it
    del xml_file
    xml_file = project_dir.file_with('.reahlproject', '''
<project type="egg">
<distpackage type="deb">
<sshdirectory host="localhost1" destination="/a/b"/>
<sshdirectory host="localhost2" login="someusername" destination="/a/c"/>
</distpackage>
</project>
''')
    project = Project.from_file(workspace, project_dir.name)

    assert isinstance(project, Project)

    [package] = project.packages_to_distribute
    assert isinstance(package, DebianPackage)
    assert package.project is project

    [repository1, repository2] = package.repositories
    assert repository1.host == 'localhost1'
    assert repository1.login == os.environ.get('USER','')
    assert repository1.destination == '/a/b'
    assert repository2.host == 'localhost2'
    assert repository2.login == 'someusername'
    assert repository2.destination == '/a/c'


def test_setup_project_file_queries():
    workspace_dir = temp_dir()
    project_dir = workspace_dir.temp_dir()
    project_filename = os.path.join(project_dir.name, '.reahlproject')
    project_source = project_dir.sub_dir('this')
    project_source_init = project_source.file_with('__init__.py', '')
    project_package1 = project_source.sub_dir('pack1')
    project_package1_init = project_package1.file_with('__init__.py', '')
    project_package2 = project_source.sub_dir('pack2')
    project_package2_init = project_package2.file_with('__init__.py', '')
    project_egg = project_dir.file_with('projegg.py', '')
    project_dev = project_source.sub_dir('proj_dev')

    @stubclass(Project)
    class ProjectStub:
        version = VersionNumber('1.2.5')

    @stubclass(Workspace)
    class WorkspaceStub:
        directory = workspace_dir.name
        project_name = 'proj'
        projects = []
        def project_named(self, name):
            return ProjectStub()
        def has_project_named(self, name):
            return True
    workspace = WorkspaceStub()

    # Case where the file does not exist
    assert not os.path.exists(project_filename)
    with expected(NotAValidProjectException):
        Project.from_file(workspace, project_dir.name)

    # Case where the file exists, but is empty
    xml_file = project_dir.file_with('.reahlproject', '')
    with expected(InvalidProjectFileException):
        Project.from_file(workspace, project_dir.name)

    # Case where the file exists with stuff in it
    del xml_file
    xml_file = project_dir.file_with('.reahlproject', '''
<project type="egg" packagedata="included">
<namespaces>
<package name="this"/>
</namespaces>

<tag name="sometag"/>

<distpackage type="deb">
<sshdirectory host="localhost1" destination="/a/b"/>
</distpackage>

<version number="0.0">
  <deps purpose="run">
    <egg name="reahl-xmlreader-run"/>
  </deps>
</version>

<deps purpose="test">
<egg name="reahl-xmlreader-test"/>
</deps>

<deps purpose="build">
<egg name="reahl-xmlreader-build"/>
</deps>

<script name="script1" locator="some script"/>
<script name="script2" locator="some other script"/>

<export entrypoint="entrypoint name 1" name="name1" locator="locator1"/>
<export entrypoint="entrypoint name 2" name="name2" locator="locator2"/>

<excludepackage name="this.pack2"/>

<pythonpath path="stuff"/>
<pythonpath path="stuff2"/>

</project>
''')
    project = Project.from_file(workspace, project_dir.name)

    # Default Metadata queries that will com for setup.py:
    assert project.project_name == os.path.basename(project_dir.name)
    assert str(project.version) == '0.0'

    @stubclass(ProjectMetadata)
    class MetadataStub:
        @property
        def version(self):
            return VersionNumber('3.1.2a1-ubuntu1')
        @property
        def project_name(self):
            return 'test-proj'

    project.metadata = MetadataStub()
    assert str(project.version_for_setup()) == '3.1.2a1'
    assert project.project_name == 'test-proj'

    packages = project.packages_for_setup()
    assert packages == ['this','this.pack1']
    assert project.py_modules_for_setup() == []
    assert project.include_package_data == True
    assert project.namespace_packages_for_setup() == ['this']

    expected_value = ['reahl-xmlreader-run>=1.2,<1.3']
    actual = project.run_deps_for_setup()
    assert actual ==  expected_value

    expected_value = ['reahl-xmlreader-test>=1.2,<1.3']
    actual = project.test_deps_for_setup()
    assert actual ==  expected_value

    expected_value = ['reahl-xmlreader-build>=1.2,<1.3']
    actual = project.build_deps_for_setup()
    assert actual ==  expected_value

    assert project.test_suite_for_setup() == 'this.proj_dev'

    expected_value = {'console_scripts':   ['script1 = some script', 'script2 = some other script'],
                'entrypoint name 2': ['name2 = locator2'],
                'reahl.eggs':        ['Egg = reahl.component.eggs:ReahlEgg'],
                'entrypoint name 1': ['name1 = locator1'],
                'reahl.versiondeps.0.0': ['reahl-xmlreader-run = egg:_'],
                'reahl.versions': ['0.0 = 0.0']
                }

    assert project.python_path == ['stuff','stuff2']

    assert project.tags == ['sometag', 'component', 'toplevel']


def test_egg_project_file_queries():
    workspace_dir = temp_dir()
    project_dir = workspace_dir.temp_dir()
    project_filename = os.path.join(project_dir.name, '.reahlproject')
    @stubclass(Workspace)
    class WorkspaceStub:
        directory = workspace_dir.name
    workspace = WorkspaceStub()

    # Case where the file exists with stuff in it
    xml_file = project_dir.file_with('.reahlproject', '''
<project type="egg" basket="some-basket">
<distpackage type="deb">
<sshdirectory host="localhost1" destination="/a/b"/>
<sshdirectory host="localhost2" login="someusername" destination="/a/c"/>
</distpackage>
</project>
''')
    project = Project.from_file(workspace, project_dir.name)

    assert isinstance(project, EggProject)
    assert project.basket_name == 'some-basket'

    [package] = project.packages_to_distribute
    assert isinstance(package, DebianPackage)
    assert package.project is project

    [repository1, repository2] = package.repositories
    assert repository1.host == 'localhost1'
    assert repository1.login == os.environ.get('USER', '')
    assert repository1.destination == '/a/b'
    assert repository2.host == 'localhost2'
    assert repository2.login == 'someusername'
    assert repository2.destination == '/a/c'




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


# -- Tests for dependencies
def test_types_of_dependencies():
    @stubclass(Workspace)
    class WorkspaceStub:
        def __init__(self, contains_project):
            self.contains_project = contains_project
        def project_named(self, name):
            return ProjectStub('proj-name', '2.1')
        def has_project_named(self, name):
            return True

    @stubclass(ChickenProject)
    class ChickenProjectStub:
        def contains_project_named(self, name):
            return True

    @stubclass(EggProject)
    class ProjectStub:
        def __init__(self, name, version, in_same_chicken=False, also_in_workspace=False):
            self.project_name = name
            self.version = VersionNumber(version)
            self.in_same_chicken = in_same_chicken
            self.workspace = WorkspaceStub(also_in_workspace)
        @property
        def chicken_project(self):
            return ChickenProjectStub() if self.in_same_chicken else None

    internal_dep = Dependency(ProjectStub('test-proj', '1.1', in_same_chicken=True), 'one')
    nonversioned_dep = Dependency(ProjectStub('test-proj', '1.1'), 'one', ignore_version=True)
    external_dep = Dependency(ProjectStub('test-proj', '1.1'), 'one')
    external_dep_in_workspace = Dependency(ProjectStub('test-proj', '1.1', also_in_workspace=True), 'one')
    thirdparty_dep = ThirdpartyDependency(ProjectStub('test-proj', '1.1'), 'one')

    # Case: for eggs
    actual = internal_dep.as_string_for_egg()
    assert actual == 'one>=1.1,<1.2'

    actual = nonversioned_dep.as_string_for_egg()
    assert actual == 'one'

    actual = external_dep.as_string_for_egg()
    assert actual == 'one>=2.1,<2.2'

    actual = external_dep_in_workspace.as_string_for_egg()
    assert actual == 'one>=2.1,<2.2'

    actual = thirdparty_dep.as_string_for_egg()
    assert actual == 'one'

    # Case: for debs
    actual = internal_dep.as_string_for_deb()
    assert actual == 'python-one (>=1.1), python-one (<<1.2)'

    actual = nonversioned_dep.as_string_for_deb()
    assert actual == 'python-one'

    actual = external_dep.as_string_for_deb()
    assert actual == 'python-one (>=2.1), python-one (<<2.2)'

    actual = external_dep_in_workspace.as_string_for_deb()
    assert actual == 'python-one (>=2.1), python-one (<<2.2)'

    actual = thirdparty_dep.as_string_for_deb()
    assert actual == ''


def test_types_of_versions():
    @stubclass(EggProject)
    class ProjectStub:
        @property
        def chicken_project(self):
            return None


    alpha_dep = Dependency(ProjectStub(), 'one', version='1.2.5a1-1')
    normal_dep = Dependency(ProjectStub(), 'one', version='1.2.5-1')

    # Case: for eggs
    actual = alpha_dep.as_string_for_egg()
    assert actual == 'one>=1.2.5a1,<1.3'

    actual = normal_dep.as_string_for_egg()
    assert actual == 'one>=1.2,<1.3'

    # Case: for debs
    actual = alpha_dep.as_string_for_deb()
    assert actual == 'python-one (>=1.2), python-one (<<1.3)'

    actual = normal_dep.as_string_for_deb()
    assert actual == 'python-one (>=1.2), python-one (<<1.3)'



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


