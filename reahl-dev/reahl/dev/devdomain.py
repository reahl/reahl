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

"""This module houses the main classes used to understand and manipulate Reahl projects in development."""

import os
import sys
import re
import glob
import os.path
import shutil
import subprocess
import logging
import pathlib
import textwrap
import email.utils
from contextlib import contextmanager
import datetime
import pkgutil
from tempfile import TemporaryFile
import collections
import json
import configparser
import tzlocal

try:
    from setuptools.config.setupcfg import read_configuration
except ImportError:
    from setuptools.config import read_configuration

import pkg_resources
import toml
import babel
import setuptools
from xml.parsers.expat import ExpatError

from reahl.component.shelltools import Executable
from reahl.component.exceptions import ProgrammerError
from reahl.component.eggs import ReahlEgg

from reahl.dev.exceptions import NoException, StatusException, AlreadyUploadedException, NotAValidProjectException, \
    InvalidProjectFileException, NotUploadedException, NotVersionedException, NotCheckedInException, \
    MetaInformationNotAvailableException, AlreadyDebianisedException, \
    MetaInformationNotReadableException, UnchangedException, NeedsNewVersionException, \
    NotBuiltAfterLastCommitException, NotBuiltException, NotSignedException

class ProjectNotFound(Exception):
    pass

class InvalidXMLException(Exception):
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
        self.repositories = []

class PythonSourcePackage(DistributionPackage):
    """A PythonSourcePackage is an egg as built with setup sdist."""
    @classmethod
    def get_xml_registration_info(cls):
        return ('distpackage', cls, 'sdist')

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
    def is_built(self):
        return self.project.distribution_egg_repository.is_uploaded(self)

    @property
    def is_signed(self):
        return self.project.distribution_egg_repository.is_signed(self)

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

    def last_built_after(self, when):
        return self.project.distribution_egg_repository.is_uploaded_after(self, when)

    @property
    def files_to_distribute(self):
        return self.project.distribution_egg_repository.uploaded_files_for(self)

    @property
    def unique_id(self):
        return self.targz_filename


class PythonWheelPackage(DistributionPackage):
    """A PythonWheelPackage is an python wheel binary package."""
    @classmethod
    def get_xml_registration_info(cls):
        return ('distpackage', cls, 'wheel')

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
    def is_built(self):
        return self.project.distribution_egg_repository.is_uploaded(self)

    @property
    def is_signed(self):
        return self.project.distribution_egg_repository.is_signed(self)

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

    def last_built_after(self, when):
        return self.project.distribution_egg_repository.is_uploaded_after(self, when)

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


class RemoteRepository:
    """A place where packages can be released to."""
    def __init__(self):
        self.local_storage = RepositoryLocalState(self)

    @property
    def knock_host(self):
        return '127.0.0.1'

    def knock(self, knocks):
        Executable('knock').check_call([self.knock_host]+knocks)

    @property
    def repository_state_directory(self):
        return self.workspace.repository_state_directory

    def is_uploaded(self, package):
        self.local_storage.read()
        return self.local_storage.is_uploaded(package)

    def upload(self, package, knocks, ignore_upload_check=False):
        if not package.is_built:
            raise NotBuiltException()
        if self.is_uploaded(package) and not ignore_upload_check:
            raise AlreadyUploadedException()
        if knocks:
            self.knock(knocks)
        self.transfer(package)
        self.local_storage.set_uploaded(package)
        self.local_storage.write()

    @property
    def unique_id(self):
        assert None, 'Not implemented'

    def transfer(self, package):
        assert None, 'Not implemented'


class PackageIndex(RemoteRepository):
    """A PyPi repository."""
    @classmethod
    def get_xml_registration_info(cls):
        return ('packageindex', cls)

    def inflate_attributes(self, reader, attributes, parent):
        self.__init__(parent.project.workspace,
                      str(attributes['repository']))

    def __init__(self, workspace, repository):
        super().__init__()
        self.workspace = workspace
        self.repository = repository

    @property
    def knock_host(self):
        return self.repository

    @property
    def unique_id(self):
        file_unsafe_id = '_'.join(['pypi', self.repository])
        return file_unsafe_id.replace(os.sep, '-')

    def transfer(self, package):
        Executable('twine').check_call(['upload', '--skip-existing', '-r', self.repository] + package.files_to_distribute)


class SshRepository(RemoteRepository):
    """A simple Repository for uploading debian or egg packages to via ssh. Uploading merely means to scp all the necessary
       debian packaging files to a directory on the remote host."""
    @classmethod
    def get_xml_registration_info(cls):
        return ('sshdirectory', cls)

    def inflate_attributes(self, reader, attributes, parent):
        self.__init__(parent.project.workspace,
                      str(attributes['host']),
                      str(attributes.get('login', os.environ.get('USER', ''))) or None,
                      str(attributes['destination']) or None)

    def __init__(self, workspace, host, login, destination):
        super().__init__()
        self.workspace = workspace
        self.host = host
        self.login = login or ''
        self.destination = destination

    @property
    def knock_host(self):
        return self.host

    def transfer(self, package):
        files = package.files_to_distribute
        Executable('scp').check_call(files+['%s@%s:%s' % (self.login, self.host, self.destination)])

    @property
    def unique_id(self):
        file_unsafe_id = '_'.join([self.login, self.host, self.destination])
        return file_unsafe_id.replace(os.sep, '-')


class LocalRepository:
    def __init__(self, root_directory):
        self.root_directory = root_directory
        self.ensure_directory(root_directory)

    def ensure_directory(self, directory_name):
        if not os.path.isdir(directory_name):
            os.mkdir(directory_name)

    def upload(self, package, knocks):
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

    def is_signed(self, package):
        result = True
        signature_file = os.path.join(self.root_directory, package.sign_filename)
        files_to_sign = [os.path.join(self.root_directory, filename) for filename in package.filenames_to_sign]

        if not all([os.path.exists(filename) for filename in files_to_sign+[signature_file]]):
            return False

        try:
            process = Executable('gpg').run(['--batch', '--verify',  signature_file]+files_to_sign, check=True, capture_output=True, cwd=self.root_directory)
        except subprocess.CalledProcessError as ex:
            if ex.returncode == 1:
                return False
            raise

        return 'Good signature' in process.stderr.decode('utf-8')

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



class LocalAptRepository(LocalRepository):
    def build_index_files(self):
        with open( os.path.join(self.root_directory, 'Packages'), 'w' ) as packages_file:
            Executable('apt-ftparchive').check_call(['packages', '.'], cwd=self.root_directory, stdout=packages_file)

        path_name, directory_name = os.path.split(self.root_directory)
        with open( os.path.join(self.root_directory, 'Release'), 'w' ) as release_file:
            Executable('apt-ftparchive').check_call(['release', directory_name], cwd=path_name, stdout=release_file)

    def sign_index_files(self, default_key=None):
        default_key_override = ['--default-key', default_key] if default_key else []
        Executable('gpg').check_call(['-abs', '--yes']+default_key_override+['-o', 'Release.gpg', 'Release'], cwd=self.root_directory)


class EntryPointExport:
    @classmethod
    def get_xml_registration_info(cls):
        return ('export', cls, None)

    def __init__(self, entrypoint, name, locator_string):
        self.entry_point = entrypoint
        self.name = name
        self.locator = EntryPointLocator(locator_string)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'entrypoint' in attributes, 'No entrypoint specified'
        assert 'name' in attributes, 'No name specified'
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['entrypoint'], attributes['name'], attributes['locator'])

    def __str__(self):
        return '%s %s:%s' % (self.__class__.__name__, self.name, self.locator.string_spec)


class ScriptExport(EntryPointExport):
    @classmethod
    def get_xml_registration_info(cls):
        return ('script', cls, None)

    def __init__(self, name, locator_string):
        super().__init__('console_scripts', name, locator_string)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['name'], attributes['locator'])


class ReahlEggExport(EntryPointExport):
    def __init__(self, locator_string):
        super().__init__('reahl.eggs', 'Egg', locator_string)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['locator'])


class TranslationPackage(EntryPointExport):
    @classmethod
    def get_xml_registration_info(cls):
        return ('translations', cls, None)

    def __init__(self, name, locator_string):
        super().__init__('reahl.translations', name, locator_string)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'locator' in attributes, 'No locator specified'
        assert ':' not in attributes['locator'], 'Please specify only a package name'
        self.__init__(parent.project_name, attributes['locator'])

    @property
    def path(self):
        return self.locator.package_path


class ExcludedPackage:
    @classmethod
    def get_xml_registration_info(cls):
        return ('excludepackage', cls, None)

    def __init__(self, name):
        self.name = name

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(attributes['name'])


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

    
class Dependency:
    egg_type = 'egg'

    def __init__(self, project, name, version=None, ignore_version=False, version_locked=False):
        self.project = project
        self.name = name
        self.ignore_version = ignore_version
        self.is_version_locked = version_locked
        self.override_version(version)

    def override_version(self, version_string):
        self.version = VersionNumber(version_string) if version_string else None

    @classmethod
    def get_xml_registration_info(cls):
        return (cls.egg_type, cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        ignore_version = attributes.get('ignoreversion', False) == 'True'
        version_locked = attributes.get('versionlocked', False) == 'True'
        if version_locked and not parent.purpose == 'run':
            raise InvalidXMLException('<%s name="%s"> is versionlocked, but versionlocked is only allowed for purpose="run"' % \
                                      (self.get_xml_registration_info()[0], attributes['name']))
        self.__init__(parent.project, attributes['name'], attributes.get('version', None), ignore_version=ignore_version, version_locked=version_locked)

    def as_string_for_egg(self):
        if not self.ignore_version and self.version_is_available():
            version = self.exact_version()
            return '%s>=%s,<%s' % (self.name, version.lower_egg_version(), version.upper_version())
        return self.name

    def as_string_for_deb(self):
        if not self.ignore_version and self.version_is_available():
            version = self.exact_version()
            return 'python-%s (>=%s), python-%s (<<%s)' % (self.name, version.lower_deb_version(),
                                                           self.name, version.upper_version())
        return 'python-%s' % self.name

    def as_project_dependencies(self, project_list):
        try:
            return [project_list.project_named(self.name)]
        except ProjectNotFound:
            print('WARNING: Could not find a project in the workspace for dependency named %s (ignoring)' % self.name, file=sys.stderr)
            return []

    @property
    def is_internal(self):
        return self.project.chicken_project and self.project.chicken_project.contains_project_named(self.name)

    @property
    def is_in_development(self):
        return self.project.workspace.has_project_named(self.name)

    @property
    def is_installed(self):
        try:
            pkg_resources.require(self.as_string_for_egg())
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            return False
        return True

    def version_is_available(self):
        return self.is_internal or self.version or self.project.workspace.has_project_named(self.name)

    def exact_version(self):
        assert self.version_is_available(), 'No version can be determined for dependency %s' % self.name
        assert not self.ignore_version, 'Versions are ignored on dependency %s' % self.name
        if self.version:
            return self.version

        if self.is_version_locked:
            return self.version

        if self.is_internal:
            return self.project.version

        try:
            project = self.project.workspace.project_named(self.name)
            return project.version
        except ProjectNotFound:
            return None


class ThirdpartyDependency(Dependency):
    egg_type = 'thirdpartyegg'

    def __init__(self, project, name, min_version=None, max_version=None, only_before_python_version=None):
        super().__init__(project, name, version=min_version)
        self.max_version = VersionNumber(max_version) if max_version else None
        self.only_before_python_version = only_before_python_version

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(parent.project, attributes['name'], min_version=attributes.get('minversion', None),
                                                          max_version=attributes.get('maxversion', None),
                                                          only_before_python_version=attributes.get('only_before_python_version', None))

    @property
    def min_version(self):
        return self.version

    def as_string_for_deb(self):
        return ''

    def as_string_for_egg(self):
        requirement_string = self.name
        if self.min_version:
            requirement_string += '>=%s' % self.min_version
        if self.max_version:
            comma = ',' if self.min_version else ''
            requirement_string += '%s<%s' % (comma, self.max_version)
        if self.only_before_python_version:
            requirement_string += ';python_version<"%s"' % self.only_before_python_version
        return requirement_string

      
class XMLDependencyList(list):
    """Purely for reading related dependencies from XML."""
    def __init__(self, project, purpose, version_entry=None):
        super().__init__()
        self.workspace = project.workspace
        self.project = project
        self.purpose = purpose
        self.version_entry = version_entry

    @classmethod
    def get_xml_registration_info(cls):
        return ('deps', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'purpose' in attributes, 'No purpose specified'
        if isinstance(parent, VersionEntry):
            version_entry = parent
            project = version_entry.project
        else:
            version_entry = None
            project = parent
        self.__init__(project, attributes['purpose'], version_entry=version_entry)

    def inflate_child(self, reader, child, tag, parent):
        assert isinstance(child, Dependency), 'Got %s, expected a dependency' % child
        if self.version_entry and child.is_version_locked:
            if self.version_entry.version.is_alpha_version():
                child_version = self.version_entry.version
            else:
                child_version = self.version_entry.version.as_major_minor()
            child.override_version(str(child_version))
        self.append(child)



class VersionDependencyEntryPointEntry(EntryPointExport):
    def __init__(self, version, dependency):
        encoded_max_version = ''
        try:
            if dependency.max_version:
                encoded_max_version = ' [%s]' % dependency.max_version
        except AttributeError:
            pass

        locator = '%s:%s%s' % (dependency.egg_type, dependency.version if dependency.version else '_', encoded_max_version )
        super(VersionDependencyEntryPointEntry, self).__init__('reahl.versiondeps.%s' % version, dependency.name, locator)


class VersionEntry(object):
    """Dependencies and migrations for a version of a project."""
    def __init__(self, project, version):
        super(VersionEntry, self).__init__()
        self.project = project
        self.version = VersionNumber(version)
        if not self.version.is_alpha_version() and self.version != self.version.as_major_minor():
            raise ProgrammerError('Patch version %s specified for %s. You can only register versions of the form major.minor (unless the patch version includes an alpha indicator)' % (version, project.project_name))

        self.run_dependencies = []
        self.migrations = []

    def as_entry_points(self):
        return [EntryPointExport('reahl.versions', str(self.version), str(self.version))] + \
               [VersionDependencyEntryPointEntry(self.version, d) for d in self.run_dependencies] + \
               self.migrations

    @classmethod
    def get_xml_registration_info(cls):
        return ('version', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'number' in attributes, 'No version number specified'
        self.__init__(parent, attributes['number'])

    def inflate_child(self, reader, child, tag, parent):
        assert isinstance(child, XMLDependencyList) or isinstance(child, MigrationList), 'Got %s, expected deps or migrations' % child
        if isinstance(child, XMLDependencyList) and child.purpose == 'run':
            self.run_dependencies = child
        if isinstance(child, MigrationList):
            self.migrations = child


class ExtrasList(list):
    """Purely for reading extras dependencies from XML."""
    def __init__(self, project, name):
        super().__init__()
        self.workspace = project.workspace
        self.project = project
        self.name = name

    @classmethod
    def get_xml_registration_info(cls):
        return ('extras', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(parent, attributes['name'])

    def inflate_child(self, reader, child, tag, parent):
        assert isinstance(child, Dependency), 'Got %s, expected a dependency' % child
        self.append(child)


class ConfigurationSpec(EntryPointExport):
    def __init__(self, locator_string):
        super().__init__('reahl.configspec', 'config', locator_string)

    @classmethod
    def get_xml_registration_info(cls):
        return ('configuration', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['locator'])


class ScheduledJobSpec(EntryPointExport):
    def __init__(self, locator_string):
        super().__init__('reahl.scheduled_jobs', locator_string, locator_string)

    @classmethod
    def get_xml_registration_info(cls):
        return ('schedule', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['locator'])


class OrderedPersistedClass:
    def __init__(self, locator_string, order, entry_point):
        self.entry_point = entry_point
        self.locator = EntryPointLocator(locator_string)
        self.order = order

    @property
    def name(self):
        return str(self.order)

    @classmethod
    def get_xml_registration_info(cls):
        return ('class', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'locator' in attributes, 'No locator specified'
        self.__init__(attributes['locator'], len(parent), parent.entry_point)


class OrderedClassesList(list):
    @property
    def entry_point(self):
        raise ProgrammerError('subclasses must provide this')

    def inflate_child(self, reader, child, tag, parent):
        assert isinstance(child, OrderedPersistedClass), 'Got %s, expected a class' % child
        self.append(child)


class PersistedClassesList(OrderedClassesList):
    """Purely for reading a list of persisted classes XML."""
    @property
    def entry_point(self):
        return 'reahl.persistlist'

    @classmethod
    def get_xml_registration_info(cls):
        return ('persisted', cls, None)


class MigrationList(OrderedClassesList):
    """Purely for reading a list of migration classes XML."""
    def __init__(self, version_entry):
        super(MigrationList, self).__init__()
        self.version_entry = version_entry

    def inflate_attributes(self, reader, attributes, parent):
        assert isinstance(parent, VersionEntry), '%s is located in %s, expected to be in a %s' % (self.__class__.__name__, parent, VersionEntry)
        self.__init__(parent)

    @property
    def entry_point(self):
        return 'reahl.migratelist.%s' % self.version_entry.version

    @classmethod
    def get_xml_registration_info(cls):
        return ('migrations', cls, None)


class EntryPointLocator:
    def __init__(self, string_spec):
        self.string_spec = string_spec
    @property
    def package_name(self):
        return self.string_spec.split(':')[0]
    @property
    def package_path(self):
        return self.package_name.replace('.', os.path.sep)
    @property
    def class_name(self):
        return self.string_spec.split(':')[-1]


class NamespaceEntry:
    def __init__(self, name):
        self.name = name

    @classmethod
    def get_xml_registration_info(cls):
        return ('package', cls, None)

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(attributes['name'])

    @property
    def path(self):
        return EntryPointLocator(self.name).package_path


class NamespaceList(list):
    @classmethod
    def get_xml_registration_info(cls):
        return ('namespaces', cls, None)

    def inflate_child(self, reader, child, tag, parent):
        assert isinstance(child, NamespaceEntry), 'Got %s, expected a NamespaceEntry' % child
        self.append(child)


class NoBasket:
    def __init__(self, workspace):
        self.workspace = workspace
        self.project_name = 'NO BASKET'


class ExtraPath:
    @classmethod
    def get_xml_registration_info(cls):
        return ('pythonpath', cls, None)

    def __init__(self, path):
        self.path = path

    def inflate_attributes(self, reader, attributes, parent):
        assert 'path' in attributes, 'No path specified'
        self.__init__(attributes['path'])



class ProjectTag:
    @classmethod
    def get_xml_registration_info(cls):
        return ('tag', cls, None)

    def __init__(self, name):
        self.name = name

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(attributes['name'])



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

    def info_readable(self):
        if self.project.chicken_project:
            return self.project.chicken_project.info_readable()
        return True

    def info_completed(self):
        if self.project.chicken_project:
            return self.project.chicken_project.info_completed()
        return True

    def get_url_for(self, project):
        if self.project.chicken_project:
            return self.project.chicken_project.get_url_for(project)
        return 'No url provided'

    def get_description_for(self, project):
        if self.project.chicken_project:
            return self.project.chicken_project.get_description_for(project)
        return 'No description provided'

    def get_long_description_for(self, project):
        if self.project.chicken_project:
            return self.project.chicken_project.get_long_description_for(project)
        return 'No description provided'

    @property
    def maintainer_name(self):
        if self.project.chicken_project:
            return self.project.chicken_project.maintainer_name
        return 'No maintainer provided'

    @property
    def maintainer_email(self):
        if self.project.chicken_project:
            return self.project.chicken_project.maintainer_email
        return 'No maintainer provided'


class MetaInfo:
    @classmethod
    def get_xml_registration_info(cls):
        return ('info', cls, None)

    def __init__(self, name):
        self.name = name

    def inflate_attributes(self, reader, attributes, parent):
        assert 'name' in attributes, 'No name specified'
        self.__init__(attributes['name'])

    def inflate_text(self, reader, text, parent):
        self.contents = text

        
class SetupMetadata(ProjectMetadata):
    def __init__(self, project, config):
        super().__init__(project)
        self.config = config

    @property
    def project_name(self):
        return self.config['metadata']['name']

    @property
    def version(self):
        return self.config['metadata']['version']


class DebianPackageMetadata(ProjectMetadata):
    def __init__(self, parent, url=None):
        super().__init__(parent)
        self.url = url

    def __str__(self):
        return 'Debian package metadata provider'

    @classmethod
    def get_xml_registration_info(cls):
        return ('metadata', cls, 'debian')

    def inflate_attributes(self, reader, attributes, parent):
        assert 'url' in attributes.keys(), 'No url specified for project in %s' % parent.directory
        self.__init__(parent, attributes['url'])
        self.debian_control = DebianControl(os.path.join(self.project.directory, 'debian', 'control'))

    @property
    def changelog(self):
        try:
            filename = os.path.join(self.directory, 'debian', 'changelog')
            return DebianChangelog(filename)
        except IOError:
            return None

    @property
    def project_name(self):
        if self.changelog:
            deb_name = self.changelog.package_name
            assert deb_name.startswith('python-')
            return deb_name[len('python-'):]
        else:
            logging.warning('Project not debianised, using directory name for project name')
            print(':::%s' % self.directory)
            return os.path.basename(self.directory)

    @property
    def version(self):
        return VersionNumber(str(self.changelog.version))

    def get_long_description_for(self, project):
        return self.debian_control.get_long_description_for('python-%s' % project.project_name).replace(' . ', '\n\n')

    def get_description_for(self, project):
        return self.debian_control.get_short_description_for('python-%s' % project.project_name)

    def get_url_for(self, project):
        return self.url

    @property
    def maintainer_name(self):
        return self.debian_control.maintainer_name

    @property
    def maintainer_email(self):
        return self.debian_control.maintainer_email

    @property
    def deb_package_name(self):
        return 'python-%s' % self.project_name

    def generate_deb_substvars(self):
        to_do = [self.project]
        if self.project.has_children:
            to_do = self.project.egg_projects

        for current_project in to_do:
            current_vars = SubstvarsFile('debian/python-%s.substvars' % current_project.project_name)
            current_vars.read()
            current_vars['reahl:Depends'] = ', '.join([i.as_string_for_deb() for i in current_project.run_deps
                                                       if i.as_string_for_deb()])
            current_vars.write()

    def info_readable(self):
        return self.info_completed()

    def info_completed(self):
        return self.changelog is not None

    def debianise(self):
        if self.info_completed():
            raise AlreadyDebianisedException()

        import tempfile
        deb_dir = os.path.join(tempfile.gettempdir(), 'python-%s-0.1.0' % self.project.project_name)
        if os.path.isdir(deb_dir):
            shutil.rmtree(deb_dir)
        os.mkdir(deb_dir)

        dh_make_params = ['--native --defaultless --single --copyright GPL']
        if self.project.workspace.dh_make_directory:
            dh_make_params[0] += ' --templates %s' % self.project.workspace.dh_make_directory

        Executable('dh_make').check_call(dh_make_params, cwd=deb_dir, shell=True)

        shutil.move(os.path.join(deb_dir, 'debian'), os.path.join(self.project.directory, 'debian'))
        shutil.rmtree(deb_dir)
        return 0

# bootstrap.py-begin
class DebianChangelog:
    package_name_regex = '(?P<package_name>[a-z][a-z0-9\-]*)'
    version_regex = '\((?P<version>[a-zA-Z\.0-9\-]+)\)'
    heading_regex = '^%s\s+%s.*$' % (package_name_regex, version_regex)

    def __init__(self, filename):
        self.filename = filename

    def parse_heading_for(self, element):
        with open(self.filename) as changelog_file:
            for line in changelog_file:
                if line.strip():
                    match = re.match(self.heading_regex, line)
                    assert match, 'Cannot parse changelog file: %s' % self.filename
                    return match.group(element)

    @property
    def package_name(self):
        return self.parse_heading_for('package_name')

    @property
    def version(self):
        return self.parse_heading_for('version')
# bootstrap.py-end


class DebianControl:
    def __init__(self, filename):
        self.filename = filename

    @property
    def stanzas(self):
        stanzas = []
        current_stanza = ''
        with open(self.filename) as control_file:
            for line in control_file:
                if not line.strip():
                    if current_stanza:
                        stanzas.append(email.message_from_string(current_stanza))
                        current_stanza = ''
                else:
                    current_stanza += line
        return stanzas

    @property
    def source_stanza(self):
        [source] = [stanza for stanza in self.stanzas if 'Source' in stanza]
        return source

    def get_package_stanza(self, package_name):
        try:
            [stanza] = [stanza for stanza in self.stanzas
                        if stanza.get('Package', None) == package_name]
            return stanza
        except ValueError:
            raise NotAValidProjectException('Could not find a stanza for a package named %s in debian control file %s' % \
                                            (package_name, self.filename))

    @property
    def maintainer_name(self):
        return email.utils.parseaddr(self.source_stanza['Maintainer'])[0]

    @property
    def maintainer_email(self):
        return email.utils.parseaddr(self.source_stanza['Maintainer'])[1]

    def get_long_description_for(self, package_name):
        description_field = self.get_package_stanza(package_name)['Description']
        return ''.join([line.strip()+' ' for line in description_field.split('\n')[1:]])

    def get_short_description_for(self, package_name):
        description_field = self.get_package_stanza(package_name)['Description']
        return description_field.split('\n')[0]


class Project:
    """Instances of Project each represent a Reahl project in a development environment.
    """

    def __str__(self):
        return '<%s>' % self.get_xml_registration_info()[0]

    @classmethod
    def from_file(cls, workspace, directory):
        setup_cfg_filename = os.path.join(directory, 'setup.cfg')
        if os.path.isfile(setup_cfg_filename):
            config = configparser.ConfigParser()
            config.read(setup_cfg_filename)
            project = Project(workspace, directory, metadata=SetupMetadata(None, config))
        else:
            raise NotAValidProjectException('Could not find a setup.cfg in %s' % directory)

        return project

    def __init__(self, workspace, directory, metadata=None):
        self.workspace = workspace
        self.directory = directory
        self.relative_directory = os.path.relpath(directory, self.workspace.directory)

        self.packages = [PythonSourcePackage(self), PythonWheelPackage(self)]
        self.python_path = []
        self.metadata = metadata or ProjectMetadata(self)

        self.namespaces = []
        self.explicitly_specified_entry_points = []
        self.excluded_packages = []
        self.include_package_data = False

        self.extras_required = {}
        self.build_deps = []
        self.test_deps = []

        self.persist_list = []
        self.version_history = []
        self.scheduled_jobs = []


    def inflate_attributes(self, reader, attributes, parent):
        workspace, directory = parent
        self.__init__(workspace, directory)

    def inflate_child(self, reader, child, tag, parent):
        if isinstance(child, ProjectTag):
            self._tags.append(child.name)
        elif isinstance(child, ProjectMetadata):
            self.metadata = child
        elif isinstance(child, ExtraPath):
            self.python_path.append(child.path)
        else:
            raise InvalidXMLException('Unexpected type read from XML: %s' % child)

    @property
    def distribution_apt_repository(self):
        return self.workspace.distribution_apt_repository

    @property
    def distribution_egg_repository(self):
        return self.workspace.distribution_egg_repository

    @property
    def packages_to_distribute(self):
        return self.packages

    @property
    def has_children(self):
        return self.project_name == 'reahl'

    @contextmanager
    def paths_set(self):
        cwd = os.getcwd()
        path = sys.path[:]
        sys.path.extend(self.python_path)
        try:
            os.chdir(self.directory)
            yield
        finally:
            sys.path[:] = path
            os.chdir(cwd)

    @property
    def locale_dirname(self):
        if not self.translation_package:
            raise DomainError(message='No reahl.translations entry point specified for project: "%s"' % (self.project_name))
        module = self.translation_package.load()
        source_paths = [i for i in module.__path__ if i.startswith(self.directory)]
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

    def info_completed(self):
        return self.metadata.info_completed()

    def info_readable(self):
        return self.metadata.info_readable()

    @property
    def project_name(self):
        return self.metadata.project_name

    @property
    def project_name_pythonised(self):
        return self.project_name.replace('-', '_')

    @property
    def version(self):
        return self.metadata.version

    def get_url_for(self, project):
        return self.metadata.get_url_for(project)

    def get_description_for(self, project):
        return self.metadata.get_description_for(project)

    def get_long_description_for(self, project):
        return self.metadata.get_long_description_for(project)

    @property
    def maintainer_name(self):
        return self.metadata.maintainer_name

    @property
    def maintainer_email(self):
        return self.metadata.maintainer_email

    def do_release_checks(self):
        if not self.is_version_controlled():
            raise NotVersionedException(self)
        elif not self.is_checked_in():
            raise NotCheckedInException(self)
        elif not self.info_completed():
            raise MetaInformationNotAvailableException(self)
        elif not self.info_readable():
            raise MetaInformationNotReadableException(self)

        if self.is_unchanged():
            raise UnchangedException(self)
        elif self.needs_new_version():
            raise NeedsNewVersionException(self)

        if not self.is_built():
            raise NotBuiltException()
        if not self.is_signed():
            raise NotSignedException()
        elif not self.latest_build_is_up_to_date_with_source():
            raise NotBuiltAfterLastCommitException()

    @property
    def status(self):
        try:
            self.do_release_checks()
            self.check_uploaded()
        except StatusException as ex:
            return ex.legend

        return NoException.legend

    def is_unchanged(self):
        return self.source_control.is_unchanged()

    def needs_new_version(self):
        return self.source_control.needs_new_version()

    def is_version_controlled(self):
        return self.source_control.is_version_controlled()

    def is_checked_in(self):
        return self.source_control.is_checked_in()

    def latest_build_is_up_to_date_with_source(self):
        last_commit_time = self.source_control.last_commit_time

        is_up_to_date = True
        for i in self.packages_to_distribute:
            is_up_to_date &= i.last_built_after(last_commit_time)
        return is_up_to_date

    def build(self, sign=True):
        assert self.packages_to_distribute, 'For %s: No <package>... listed in setup.cfg, nothing to do.' % self.project_name
        for i in self.packages_to_distribute:
            i.build(sign=sign)

    def sign(self):
        assert self.packages_to_distribute, 'For %s: No <package>... listed in setup.cfg, nothing to do.' % self.project_name
        for i in self.packages_to_distribute:
            i.sign()
            
    def is_built(self):
        is_built = True
        for i in self.packages_to_distribute:
            is_built &= i.is_built
        return is_built

    def is_signed(self):
        is_signed = True
        for i in self.packages_to_distribute:
            is_signed &= i.is_signed
        return is_signed
    
    def upload(self, knocks=[], ignore_release_checks=False, ignore_upload_check=False):
        try:
           self.do_release_checks()
        except StatusException as ex:
           if not ignore_release_checks:
              raise
           else:
              logging.warning( ex )
        for i in self.packages_to_distribute:
            for repo in i.repositories:
                repo.upload(i, knocks, ignore_upload_check=ignore_upload_check)

    def check_uploaded(self):
        for i in self.packages_to_distribute:
            for repo in i.repositories:
                if not repo.is_uploaded(i):
                    raise NotUploadedException(i)

    def mark_as_released(self):
        self.do_release_checks()
        self.check_uploaded()
        self.source_control.place_tag(str(self.version))

    def get_project_in_directory(self, directory):
        try:
            return self.workspace.project_in(directory)
        except ProjectNotFound:
            return Project.from_file(self.workspace, directory)

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

    def get_build_sources(self):
        self.setup(['egg_info'])

        sources = []
        sources_filename = os.path.join(self.egg_info_directory, 'SOURCES.txt')

        with open(sources_filename) as in_file:
            for line in in_file:
                sources.append(line)
        return sources

    @property
    def egg_info_directory(self):
        return os.path.join(self.directory, '%s.egg-info' % self.project_name_pythonised)

    def list_missing_dependencies(self, for_development=False):
        all_deps = self.run_deps_for_setup()
        if for_development:
            all_deps = self.run_deps_for_setup()+self.build_deps_for_setup()+self.test_deps_for_setup()+[i for extras in self.extras_require_for_setup().values() for i in extras]
        def is_installed(dep):
            try:
               pkg_resources.require(dep)
            except:
               return False
            return True
        def is_in_workspace(dep):
            name = dep.split('<')[0].split('>')[0]
            return self.workspace.has_project_named(name)
        missing = [dep for dep in all_deps if (not is_installed(dep)) and (not is_in_workspace(dep))]
        return [i.replace(' ', '') for i in missing]

    def setup(self, setup_command):
        return self.run_python('pip', setup_command)
    
    def run_python(self, module, args):
        with self.paths_set():
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

    @property
    def setup_cfg_filename(self):
        return os.path.join(self.directory, 'setup.cfg')

    @property
    def run_deps(self):
        if self.version_history:
            return list(sorted(self.version_history, key=lambda x : pkg_resources.parse_version(str(x.version))))[-1].run_dependencies
        else:
            return []

    def run_deps_for_setup(self):
        return [dep.as_string_for_egg() for dep in self.run_deps]

    def build_deps_for_setup(self):
        deps = [dep.as_string_for_egg() for dep in self.build_deps]
        if os.path.isfile(self.pyproject_toml_filename):
            toml_config = toml.load(self.pyproject_toml_filename)
            deps += toml_config['build-system']['requires']
        return list(sorted(set(deps)))

    @property
    def setup_cfg(self):
        if pathlib.Path(self.setup_cfg_filename).exists():
          return read_configuration(self.setup_cfg_filename)
        return {}

    def test_deps_for_setup(self):
        reahlproject_deps = [dep.as_string_for_egg() for dep in self.test_deps]
        setup_cfg_deps = self.setup_cfg.get('options', {}).get('tests_require', [])
        return reahlproject_deps + setup_cfg_deps

    def packages_for_setup(self):
        exclusions = [i.name for i in self.excluded_packages]
        exclusions += ['%s.*' % i.name for i in self.excluded_packages]
        # Adding self.namespace_packages... is to work around https://github.com/pypa/setuptools/issues/97
        ns_packages = self.namespace_packages_for_setup()
        packages = list(set([i for i in setuptools.find_packages(where=self.directory, exclude=exclusions)]+ns_packages))
        packages.sort()
        return packages

    def namespace_packages_for_setup(self):
        return [i.name for i in self.namespaces]  # Note: this has to return non-str strings for setuptools!

    def py_modules_for_setup(self):
        return list(set([i[1] for i in pkgutil.iter_modules(['.']) if not i[2]])-{'setup'})

    def package_data_for_setup(self):
        return {'': ['*/LC_MESSAGES/*.mo']}

    @property
    def test_suite(self):
        directories_to_search = [self.directory]+[os.path.join(self.directory,i.path) for i in self.namespaces]

        for directory in directories_to_search:
            for name in os.listdir(directory):
                full_path = os.path.join(directory,name)
                if os.path.isdir(full_path) and name.endswith('_dev'):
                    path = full_path[len(self.directory)+1:]
                    return '.'.join(path.split(os.path.sep))

        return 'tests'

    def test_suite_for_setup(self):
        return self.test_suite

    def extras_require_for_setup(self):
        return dict( [ (name, [dep.as_string_for_egg() for dep in dependencies])
                       for name, dependencies in self.extras_required.items()] )

    @property
    def extras(self):
        extras = []
        for dependencies in self.extras_required.values():
            extras.extend(dependencies)
        return extras

    def debinstall(self, args):
        root = os.path.join(self.directory, 'debian', 'python-%s' % self.project_name)
        executable = '/usr/bin/python'
        build_directory = os.path.join(self.workspace.build_directory, self.project_name)
        self.setup(['build', '-b', build_directory, 'build_scripts', '-e', executable, 'install', '--single-version-externally-managed', '--root=%s' % root, '--prefix=/usr'])

    def distributed_python_files(self):
        package_dirs = [i.replace('.', os.sep) for i in self.packages_for_setup()]
        py_files = set()
        for package_dir in package_dirs:
            for dirname, dirnames, filenames in os.walk(package_dir):
                for filename in filenames:
                    if filename.endswith('.py'):
                        py_files.add(os.path.join(dirname, filename))
        return list(py_files)


class SetupCommandFailed(Exception):
    def __init__(self, command):
        super().__init__(command)
        self.command = command


class SetupMonitor:
    def __init__(self):
        self.captured_stdout = []

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.encoding = sys.stdout.encoding # input() raises (TypeError: bad argument type for built-in operation) without this defined. See bug 1442104
        self.errors = sys.stdout.errors     # input() raises (TypeError: bad argument type for built-in operation) without this defined. See bug 1442104
        sys.stdout = self
        return self

    def write(self, line_to_write):
        self.captured_stdout.append(line_to_write)
        self.original_stdout.write(line_to_write)

    def flush(self):
        self.original_stdout.flush()

    def isatty(self):
        return self.original_stdout.isatty()

    def __exit__(self, *args):
        sys.stdout = self.original_stdout

    def check_command_status(self, commands):
        for command in commands:
            self.check(command)

    def check(self, command):
        check_method = getattr(self, 'check_%s_command' % command, None)
        if check_method and not check_method():
            raise SetupCommandFailed(command)

    def output_ends_with(self, starting, expected_end, only_up_to=None):
        if not starting in self.captured_stdout:
            return False
        start_index = self.captured_stdout.index(starting)
        for line in self.captured_stdout[start_index+1:]:
            if re.match(expected_end, line):
                return True
            if only_up_to and line.startswith(only_up_to):
                return False
        return True

    def check_build_command(self):
        return self.output_ends_with('running build\n', '[Cc]reating (tar archive|.*/WHEEL)\n')

    def check_upload_command(self):
        return self.output_ends_with('running upload\n', 'Server response (200): OK\n', only_up_to='running')

    def check_register_command(self):
        return self.output_ends_with('running register\n', 'Server response (200): OK\n', only_up_to='running')

    def check_sdist_command(self):
        return self.output_ends_with('running sdist\n', 'Creating tar archive\n')


class AddedOrderDict(collections.OrderedDict):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)


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
                if 'setup.cfg' in files:
                    project = Project.from_file(self.workspace, root)
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
                self.append(Project.from_file(self.workspace, full_dir))
            else:
                logging.getLogger(__name__).warning('Skipping %s, it does not exist anymore' % name)

    def select(self, states=None, tags=None, append=False, all_=False, negated=False):
        states = states or []
        tags = tags or []
        if append:
            selection = self.workspace.selection
        else:
            selection = ProjectList(self.workspace)

        for i in self:
            if (not negated) == (all_ or (len(set(i.tags) & set(tags))>0)):
                selection.append(i)
        return selection

    def select_one(self, directory):
        selection = ProjectList(self.workspace)
        for i in self:
            if i.directory == directory:
                selection.append(i)
                return selection

        selection.append(Project.from_file(self.workspace, directory))
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

    def select(self, states=None, tags=None, append=False, all_=False, negated=False):
        self.selection = self.projects.select(states=states, tags=tags, append=append, all_=all_, negated=negated)
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

    def update_apt_repository_index(self, sign=True):
        self.distribution_apt_repository.build_index_files()
        if sign:
            self.distribution_apt_repository.sign_index_files()


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
    def distribution_apt_repository(self):
        return LocalAptRepository(os.path.join(self.reahl_directory, 'dist'))

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


class SubstvarsFile(list):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def read(self):
        if not os.path.isfile(self.filename):
            return

        with open(self.filename) as f:
            for line in f:
                bits = line.strip().split('=')
                key = bits[0]
                value = '='.join(bits[1:])
                self[key] = value

    def write(self):
        with open(self.filename, 'w') as f:
            for key, value in self:
                f.write('%s=%s\n' % (key, value))

    def __setitem__(self, key, value):
        try:
            [pair] = [i for i in self
                      if i[0] == key]
            self.insert(self.index(pair), (key, value))
            self.remove(pair)
        except ValueError:
            self.append((key, value))

    def __getitem__(self, key):
        return dict(self)[key]

    def items(self):
        return [i for i in self]

all_xml_classes = []
