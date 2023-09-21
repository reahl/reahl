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

"""This module houses the main classes used to understand and manipulate Reahl projects in development."""

import os
import sys
import re
import glob
import os.path
import shutil
import subprocess
import logging
from contextlib import contextmanager
import datetime
from tempfile import TemporaryFile
import tzlocal
import pathlib

try:
    from setuptools.config.setupcfg import read_configuration
except ImportError:
    from setuptools.config import read_configuration

import pkg_resources
import toml
import babel
import setuptools

from reahl.component.shelltools import Executable
from reahl.component.exceptions import ProgrammerError
from reahl.component.eggs import ReahlEgg

from reahl.dev.exceptions import NotAValidProjectException

class ProjectNotFound(Exception):
    pass

class InvalidLocaleString(Exception):
    pass

class EggNotFound(Exception):
    pass


class Git:
    def __init__(self, directory):
        self.directory = directory

    @property
    def last_commit_time(self):
        with TemporaryFile(mode='w+') as out:
            with open(os.devnull, 'w') as DEVNULL:
                Executable('git').check_call('log -r -1 --pretty="%ci"'.split(), cwd=self.directory, stdout=out, stderr=DEVNULL)
                out.seek(0)
                [timestamp] = [line.replace('\n','') for line in out]
        return datetime.datetime.strptime(timestamp, '"%Y-%m-%d %H:%M:%S %z"')

    def config(self, key, value, apply_globally=False):
        with open(os.devnull, 'w') as DEVNULL:
            scope = '--global' if apply_globally else '--local'
            return_code = Executable('git').call(['config', scope, key, value], cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)
        return return_code == 0

    def is_version_controlled(self):
        return self.uses_git()

    def is_checked_in(self):
        with TemporaryFile(mode='w+') as out:
            return_code = Executable('git').call('status --porcelain'.split(), cwd=self.directory, stdout=out, stderr=out)
            out.seek(0)
            return return_code == 0 and not out.read()

    def uses_git(self):
        with TemporaryFile(mode='w+') as out:
            try:
                Executable('git').call('rev-parse --is-inside-work-tree'.split(), cwd=self.directory, stdout=out, stderr=out)
                out.seek(0)
                return out.read().replace('\n','') == 'true'
            except Exception as ex:
                logging.error('Error trying to execute "git rev-parse --is-inside-work-tree" in %s: %s' % (self.directory, ex))
            return False

    def tag(self, tag_string):
        with open(os.devnull, 'w') as DEVNULL:
            Executable('git').check_call(('tag %s' % tag_string).split(), cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)

    def get_tags(self, head_only=False):
        tags = []
        with TemporaryFile(mode='w+') as out:
            with open(os.devnull, 'w') as DEVNULL:
                head_only = ' -l --points-at HEAD' if head_only else ''
                Executable('git').check_call(('tag'+head_only).split(), cwd=self.directory, stdout=out, stderr=DEVNULL)
                out.seek(0)
                tags = [line.split()[0] for line in out if line]
        return tags

    def commit(self, message, allow_empty=False):
        with open(os.devnull, 'w') as DEVNULL:
            args = '-am "%s"' % message
            if allow_empty:
                args += ' --allow-empty'
            return_code = Executable('git').call(('commit %s' % args).split(), cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)
        return return_code == 0


class DistributionPackage:
    """A DistributionPackage is a package that may be built for distribution."""
    def __init__(self, project):
        self.project = project
        self.repositories = [PackageIndex(project.workspace, 'pypi')]

class PythonSourcePackage(DistributionPackage):
    """A PythonSourcePackage is an egg as built with setup sdist."""
    def __str__(self):
        return 'Sdist (source egg).'

    def build(self, sign=True):
        build_directory = os.path.join(self.project.workspace.build_directory, self.project.project_name)
        self.project.run_python('build', ['--sdist', '--outdir', self.project.distribution_egg_repository.root_directory])
        if sign:
            self.sign()

    def sign(self):
        self.project.distribution_egg_repository.sign_files_for(self)

    @property
    def package_files(self):
        return [self.targz_filename, self.sign_filename]

    @property
    def targz_filename(self):
        return self.targz_filename_for(self.project)

    @property
    def sign_filename(self):
        return '%s.asc' % self.targz_filename

    @property
    def filenames_to_sign(self):
        return [self.targz_filename]

    def targz_filename_for(self, project):
        return '%s-%s.tar.gz' % (project.project_name, project.version)

    @property
    def files_to_distribute(self):
        return self.project.distribution_egg_repository.uploaded_files_for(self)

    @property
    def unique_id(self):
        return self.targz_filename


class PythonWheelPackage(DistributionPackage):
    """A PythonWheelPackage is an python wheel binary package."""
    def __str__(self):
        return 'Wheel (bdist_wheel).'

    def build(self, sign=True):
        build_directory = os.path.join(self.project.workspace.build_directory, self.project.project_name)
        self.project.run_python('build', ['--wheel', '--outdir', self.project.distribution_egg_repository.root_directory])
        if sign:
            self.sign()

    def sign(self):
        self.project.distribution_egg_repository.sign_files_for(self)

    @property
    def package_files(self):
        return [self.wheel_filename, self.sign_filename]

    @property
    def wheel_filename(self):
        return self.wheel_filename_for(self.project)

    @property
    def sign_filename(self):
        return '%s.asc' % self.wheel_filename

    @property
    def filenames_to_sign(self):
        return [self.wheel_filename]

    def wheel_filename_for(self, project):
        return '%s-%s-py3-none-any.whl' % (project.project_name_pythonised, project.version)

    @property
    def files_to_distribute(self):
        return self.project.distribution_egg_repository.uploaded_files_for(self)

    @property
    def unique_id(self):
        return self.wheel_filename



class RepositoryLocalState:
    """Used by Repository objects to keep track locally of what packages have been uploaded to the Repository."""
    def __init__(self, repository):
        self.repository = repository
        self.uploaded_project_ids = set()

    def is_uploaded(self, package):
        return package.unique_id in self.uploaded_project_ids

    def set_uploaded(self, package):
        self.uploaded_project_ids.add(package.unique_id)

    @property
    def upload_state_filename(self):
        return os.path.join(self.repository.repository_state_directory, '%s.uploaded' % self.repository.unique_id )

    def read(self):
        self.uploaded_project_ids = set()
        if not os.path.exists(self.upload_state_filename):
            return
        f = open(self.upload_state_filename, 'r')
        self.uploaded_project_ids = set(f.read().splitlines())
        f.close()

    def write(self):
        f = open(self.upload_state_filename, 'w')
        f.writelines(['%s\n' % i for i in self.uploaded_project_ids])
        f.close()


class PackageIndex:
    """A PyPi repository."""
    def __init__(self, workspace, repository):
        super().__init__()
        self.local_storage = RepositoryLocalState(self)
        self.workspace = workspace
        self.repository = repository

    @property
    def repository_state_directory(self):
        return self.workspace.repository_state_directory

    def is_uploaded(self, package):
        self.local_storage.read()
        return self.local_storage.is_uploaded(package)

    def upload(self, package):
        self.transfer(package)
        self.local_storage.set_uploaded(package)
        self.local_storage.write()

    @property
    def unique_id(self):
        file_unsafe_id = '_'.join(['pypi', self.repository])
        return file_unsafe_id.replace(os.sep, '-')

    def transfer(self, package):
        Executable('twine').check_call(['upload', '--skip-existing', '-r', self.repository] + package.files_to_distribute)


class LocalRepository:
    def __init__(self, root_directory):
        self.root_directory = root_directory
        self.ensure_directory(root_directory)

    def ensure_directory(self, directory_name):
        if not os.path.isdir(directory_name):
            os.mkdir(directory_name)

    def upload(self, package):
        for filename in package.build_output_files:
            shutil.copy(filename, self.root_directory)
            
    def is_uploaded(self, package):
        result = True
        for filename in self.uploaded_files_for(package):
            result = result and os.path.isfile(filename)
        return result

    def is_uploaded_after(self, package, when):
        if not self.is_uploaded(package):
            return False
        a_file = self.uploaded_files_for(package)[0]
        return datetime.datetime.fromtimestamp(os.path.getmtime(a_file), tzlocal.get_localzone()) >= when

    def remove_uploaded(self, package):
        for filename in self.uploaded_files_for(package):
            if os.path.isfile(filename):
                os.remove(filename)

    def uploaded_files_for(self, package):
        return [os.path.join(self.root_directory, filename)
                for filename in package.package_files]

    def sign_files_for(self, package):
        sign_file = os.path.join(self.root_directory, package.sign_filename)
        files_to_sign = [os.path.join(self.root_directory, filename) for filename in package.filenames_to_sign]

        passphrase_args = []
        stdin_input = None
        passphrase = os.environ.get('GPG_PASSPHRASE', None)
        if passphrase:
            passphrase_args = ['--pinentry-mode', 'loopback', '--passphrase-fd', '0']
            stdin_input = ('%s' % passphrase).encode('utf-8')
        Executable('gpg').run(['-ab', '--yes', '-o', sign_file]+passphrase_args+files_to_sign, input=stdin_input, cwd=self.root_directory)


class VersionNumber:
    def __init__(self, version_string):
        match = re.match('^(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>[0-9a-zA-Z]+)((?P<other>[^-]+)?)(-(?P<debian_rev>.*))?)?$', version_string)
        if not match:
            raise ProgrammerError('Could not parse version string "%s"' % version_string)
        self.major = match.group('major')
        self.minor = match.group('minor')
        self.patch = match.group('patch')
        self.other = match.group('other')
        self.debian_revision = match.group('debian_rev')

    def __str__(self):
        tail_bits = []
        if self.patch:
            tail_bits += [self.patch]
        if self.debian_revision:
            tail_bits += [self.debian_revision]

        tail = ['-'.join(tail_bits)] if tail_bits else []
        return '.'.join([self.major, (self.minor+(self.other or ''))] + tail)

    def truncated(self):
        return VersionNumber('.'.join([self.major, self.minor]))

    def is_alpha_version(self):
        if not self.patch:
            return True
        return not re.match('^\d+$', self.patch)

    def upper_version(self):
        return VersionNumber('.'.join([self.major, str(int(self.minor)+1)]))

    def lower_deb_version(self):
        return self.truncated()

    def lower_egg_version(self):
        if self.is_alpha_version():
           return self.as_upstream()
        return self.truncated()

    def as_upstream(self):
        return VersionNumber('.'.join([self.major, self.minor]+([self.patch] if self.patch else [])))

    def as_major_minor(self):
        return VersionNumber('.'.join([self.major, self.minor]))

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    
class NoBasket:
    def __init__(self, workspace):
        self.workspace = workspace
        self.project_name = 'NO BASKET'


class ProjectMetadata:
    def __str__(self):
        return 'Default project metadata provider'

    def __init__(self, project):
        self.project = project

    @property
    def project_name(self):
        return os.path.basename(self.directory)

    @property
    def directory(self):
        return self.project.directory

    @property
    def version(self):
        if self.project.chicken_project:
            return self.project.chicken_project.version
        return VersionNumber('0.0')

    @property
    def extras(self):
        return {}

    
class PyprojectMetadata:
    @classmethod
    def from_file_in(cls, directory):
        pyproject_filename = pathlib.Path(directory).joinpath('pyproject.toml')
        if not pyproject_filename.exists():
            raise FileNotFoundError(str(pyproject_filename))
        config = toml.load(pyproject_filename)
        return cls(config)
        
    def __init__(self, config):
        self.config = config

    @property
    def is_complete(self):
        return 'project' in self.config
        
    @property
    def project_name(self):
        return self.config['project']['name']

    @property
    def version(self):
        return self.config['project']['version']
    
    @property
    def extras(self):
        return self.config['project'].get('optional-dependencies', {})

    
class Project:
    """Instances of Project each represent a Reahl project in a development environment.
    """

    def __str__(self):
        return '<project %s %s>' % (self.project_name, self.version)

    @classmethod
    def metadata_in(cls, directory):
        try:
            return PyprojectMetadata.from_file_in(directory)
        except FileNotFoundError:
            raise NotAValidProjectException('Could not find a complete pyproject.toml in %s' % directory)
    
    @classmethod
    def from_file_in(cls, workspace, directory):
        metadata = cls.metadata_in(directory)
            
        if metadata.is_complete:
            return Project(workspace, directory, metadata=metadata)
        else:
            raise NotAValidProjectException('Could not find a complete pyproject.toml in %s' % directory)

    def __init__(self, workspace, directory, metadata=None):
        self.workspace = workspace
        self.directory = directory

        self.packages = [PythonSourcePackage(self), PythonWheelPackage(self)]
        self.metadata = metadata or ProjectMetadata(self)

    @property
    def relative_directory(self):
        return os.path.relpath(self.directory, self.workspace.directory)
    
    @property
    def distribution_egg_repository(self):
        return self.workspace.distribution_egg_repository

    @property
    def packages_to_distribute(self):
        return self.packages

    @property
    def has_children(self):
        return 'all' in self.metadata.extras

    @property
    def egg_projects(self):
        if not self.has_children:
            return None
        all_projects_requirements = self.metadata.extras['all']
        def get_project_dir_for(requirement):
            return str(pathlib.Path(self.directory).joinpath(pkg_resources.Requirement.parse(requirement).project_name))
        return [Project.from_file_in(self.workspace, get_project_dir_for(i))
                for i in all_projects_requirements]

    @contextmanager
    def in_project_directory(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.directory)
            yield
        finally:
            os.chdir(cwd)

    @property
    def locale_dirname(self):
        if not self.translation_package:
            raise ProgrammerError('No reahl.translations entry point specified for project: "%s"' % (self.project_name))
        module = self.translation_package.load()
        source_paths = [i for i in set(module.__path__) if i.startswith(self.directory+os.path.sep)]
        [source_path] = source_paths
        return source_path

    @property
    def interface(self):
        return ReahlEgg.interface_for(pkg_resources.get_distribution(self.project_name))

    @property
    def translation_package(self):
        return self.interface.translation_package_entry_point
                            
    @property
    def locale_domain(self):
        return self.project_name

    @property
    def pot_filename(self):
        return os.path.join(self.locale_dirname, self.locale_domain)

    def extract_messages(self, args):
        if self.translation_package:
            Executable('pybabel').check_call(('extract --project=%s --version=%s --input-dirs . --output-file %s' % (self.project_name, self.version, self.pot_filename)).split(), cwd=self.directory)
        else:
            logging.warning('No reahl.translations entry point specified for project: "%s"' % (self.project_name))

    @property
    def translated_domains(self):
        if self.translation_package:
            filenames = glob.glob(os.path.join(self.locale_dirname, '*/LC_MESSAGES/*.po'))
            return {os.path.splitext(os.path.basename(i))[0] for i in filenames}
        else:
            logging.warning('No reahl.translations entry point specified for project: "%s"' % (self.project_name))
            return []

    def merge_translations(self):
        for source_dist_spec in self.translated_domains:
            try:
                source_egg = ReahlEgg.interface_for(pkg_resources.get_distribution(source_dist_spec))
            except pkg_resources.DistributionNotFound:
                raise EggNotFound(source_dist_spec)
            if not os.path.isdir(self.locale_dirname):
                os.mkdir(self.locale_dirname)
            Executable('pybabel').check_call(['update','--input-file', source_egg.translation_pot_filename,
                                              '--domain', source_egg.name,
                                              '-d', self.locale_dirname], cwd=self.directory)
            
    def compile_translations(self):
        for domain in self.translated_domains:
            Executable('pybabel').check_call(['compile',
                                              '--domain', domain,
                                              '-d', self.locale_dirname], cwd=self.directory)

    def add_locale(self, locale, source_dist_spec):
        try:
            babel.parse_locale(locale)
        except ValueError:
            raise InvalidLocaleString(locale)
        try:
            source_egg = ReahlEgg.interface_for(pkg_resources.get_distribution(source_dist_spec or self.project_name))
        except pkg_resources.DistributionNotFound:
            raise EggNotFound(source_dist_spec or self.project_name)
        Executable('pybabel').check_call(['init',
                                          '--input-file', source_egg.translation_pot_filename,
                                          '--domain', source_egg.name,
                                          '-d', self.locale_dirname,
                                          '--locale', locale], cwd=self.directory)
        return locale

    #-----------[ metadata stuff ]---------------------------------------

    @property
    def project_name(self):
        return self.metadata.project_name

    @property
    def project_name_pythonised(self):
        return self.project_name.replace('-', '_')

    @property
    def version(self):
        return VersionNumber(self.metadata.version)
    
    @property
    def extras(self):
        return self.metadata.extras

    def build(self, sign=True):
        for i in self.packages_to_distribute:
            i.build(sign=sign)

    def sign(self):
        for i in self.packages_to_distribute:
            i.sign()
            
    def upload(self):
        for i in self.packages_to_distribute:
            for repo in i.repositories:
                repo.upload(i)

    def get_project_in_directory(self, directory):
        try:
            return self.workspace.project_in(directory)
        except ProjectNotFound:
            return Project.from_file_in(self.workspace, directory)

    @property
    def basket(self):
        baskets = [i for i in self.workspace.projects
                   if i.contains(self)]
        if not baskets:
            return NoBasket(self.workspace)
        else:
            # If it breaks here, it means there is more than one basket found in the current workspace which claim
            #  that this egg belongs to them.
            # Eggs are not allowed to belong to more than one basket, but this could happen if multiple versions
            #  of an egg is checked out in the current workspace
            [basket] = baskets
            return basket

    def contains(self, other):
        return False

    def run_python(self, module, args):
        with self.in_project_directory():
            command = ['python', '-m', module] + args
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(' '.join(['Running (%s):' % os.getcwd() ] + process.args))
            out, err = process.communicate()
            sys.stdout.write(out.decode())
            sys.stderr.write(err.decode())

            return_code = process.returncode
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, command)

    @property
    def pyproject_toml_filename(self):
        return os.path.join(self.directory, 'pyproject.toml')


class DirectoryList(list):
    """Utility class used to read a list of directory names from a file on disk."""

    @classmethod
    def from_file(cls, filename):
        directories = DirectoryList()
        directories.read(filename)
        return directories

    def read(self, filename):
        f = open(filename, 'r')
        dirnames = f.read().splitlines()
        f.close()
        for name in dirnames:
            self.append(name)


class ProjectList(list):
    """A list of Projects, allowing a number of operations on such a list. These include saving the list to disk."""

    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.name_index = {}  # The dict is used to speed up queries (see project_named)

    def append(self, something, ignore_duplicates=False):
        assert ignore_duplicates or something.project_name not in self.name_index, 'Attempt to add duplicate project to project list'
        if something.project_name not in self.name_index:
            self.name_index[something.project_name] = something
            super().append(something)

    def project_in(self, directory):
        full_path = os.path.normpath(directory)
        for project in self:
            if project.directory == full_path:
                return project
        raise ProjectNotFound(full_path)

    def has_project_named(self, name):
        return name in self.name_index.keys()

    def project_named(self, name):
        # Breaking here? Maybe reahl refresh needed?
        try:
            return self.name_index[name]
        except KeyError:
            raise ProjectNotFound(name)

    @classmethod
    def from_file(cls, filename, workspace):
        projects = ProjectList(workspace)
        projects.read(filename)
        return projects

    def collect_projects(self, directories):
        for directory in directories:
            for root, dirs, files in os.walk(os.path.abspath(directory)):
                if '.reahlignore' in files:
                    ignore_list = DirectoryList.from_file(os.path.join(root, '.reahlignore'))
                    for i in ignore_list:
                        try:
                            dirs.remove(i)
                        except ValueError:
                            pass
                if 'pyproject.toml' in files and PyprojectMetadata.from_file_in(root).is_complete:
                    project = Project.from_file_in(self.workspace, root)
                    self.append(project, ignore_duplicates=True)
                    if not project.has_children:
                        dirs[:] = []  # This prunes the tree so it does not walk deeper in here

    def save(self, filename):
        pathlib.Path(pathlib.Path(filename).parent).mkdir(parents=True, exist_ok=True)
        f = open(filename, 'w')
        f.writelines(['%s\n' % i.relative_directory for i in self])
        f.close()

    def delete(self, filename):
        os.remove(filename)

    def read(self, filename):
        self[:] = []
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as f:
            project_dirs = f.read().splitlines()
        for name in project_dirs:
            full_dir = os.path.join(self.workspace.directory, name)
            if os.path.isdir(full_dir):
                self.append(Project.from_file_in(self.workspace, full_dir))
            else:
                logging.getLogger(__name__).warning('Skipping %s, it does not exist anymore' % name)

    def select(self, append=False, all_=False):
        if append:
            selection = self.workspace.selection
        else:
            selection = ProjectList(self.workspace)

        for i in self:
            selection.append(i)
        return selection

    def select_one(self, directory):
        selection = ProjectList(self.workspace)
        for i in self:
            if i.directory == directory:
                selection.append(i)
                return selection

        selection.append(Project.from_file_in(self.workspace, directory))
        return selection


class Workspace:
    """A Workspace logically contains several Projects in development. It facilitates issuing operations on sets
    of Projects, and administers the results.

    A Workspace is a directory hierarchy on disk, the projects in it are all checked out somewhere in this hierarchy.

    The workspace provides a location where all manner of administrative information can be saved for the projects
    it contains.
    """
    def __init__(self, directory):
        self.directory = directory
        self.startup_directory = os.getcwd()
        self.projects = ProjectList(self)
        self.selection = ProjectList(self)

    def get_selection_filename(self, name):
        return os.path.join(self.reahl_directory, '%s.selection' % name)

    @property
    def current_selection_filename(self):
        return os.path.join(self.reahl_directory, '%s.selection' % 'current')

    @property
    def current_projects_filename(self):
        return os.path.join(self.reahl_directory, 'workspace.projects')

    @property
    def build_directory(self):
        return os.path.join(self.reahl_directory, 'build')

    def save_selection(self, name):
        return self.selection.save(self.get_selection_filename(name))

    def read_selection(self, name):
        return self.selection.read(self.get_selection_filename(name))

    def delete_selection(self, name):
        return self.selection.delete(self.get_selection_filename(name))

    def save(self):
        self.selection.save(self.current_selection_filename)
        self.projects.save(self.current_projects_filename)

    def read_current_selection(self):
        self.selection.read(self.current_selection_filename)

    def read(self):
        self.read_current_selection()
        self.projects.read(self.current_projects_filename)

    def refresh(self, append, directories):
        directories = [os.path.normpath(os.path.expanduser(os.path.join(self.startup_directory, i))) for i in directories]

        if not append:
            self.projects = ProjectList(self)

        self.projects.collect_projects(directories or [self.directory])
        self.selection = ProjectList(self)
        self.save()

    def select(self, append=False, all_=False):
        self.selection = self.projects.select(append=append, all_=all_)
        self.save()

    def clear_selection(self):
        self.selection = ProjectList(self)
        self.save()

    def get_selection_subset(self, states=None, tags=None, append=False, all_=False, negated=False):
        return self.selection.select(states=states, tags=tags, append=append, all_=all_, negated=negated)

    def project_named(self, name):
        return self.projects.project_named(name)

    def has_project_named(self, name):
        return self.projects.has_project_named(name)

    def project_in(self, directory):
        return self.projects.project_in(directory)

    @property
    def reahl_directory(self):
        dirname = os.path.join(self.directory, '.reahlworkspace')
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return dirname

    @property
    def release_directory(self):
        dirname = os.path.join(self.reahl_directory, 'torelease')
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return dirname

    @property
    def distribution_egg_repository(self):
        return LocalRepository(os.path.join(self.reahl_directory, 'dist-egg'))

    @property
    def repository_state_directory(self):
        dirname = os.path.join(self.reahl_directory, 'uploadstate')
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return dirname

    @property
    def dh_make_directory(self):
        dirname = os.path.join(self.reahl_directory, 'dh_make')
        if not os.path.isdir(dirname):
            return None
        return dirname

    def get_saved_selections(self):
        filenames = glob.glob(os.path.join(self.reahl_directory, '*.selection'))
        return [os.path.splitext(os.path.basename(i))[0] for i in filenames]



