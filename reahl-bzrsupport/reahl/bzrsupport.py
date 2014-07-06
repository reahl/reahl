# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import subprocess
import logging
import os
import os.path
from tempfile import TemporaryFile
import datetime

# see http://packages.python.org/distribute/setuptools.html#adding-support-for-other-revision-control-systems

class ExecutableNotInstalledException(Exception):
    """ Copied reahl.component.shelltools to avoid dependency issues"""
    def __init__(self, executable_name):
        self.executable_name = executable_name
    def __str__(self):
        return 'Executable not found: %s' % self.executable_name


class Executable(object):
    """ Copied reahl.component.shelltools to avoid dependency issues"""
    
    def __init__(self, name):
        self.name = name

    @property
    def executable_file(self):
        return self.which(self.name)

    def which(self, program):
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)

        def ext_candidates(fpath):
            for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
                yield fpath + ext
            yield fpath

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                for candidate in ext_candidates(exe_file):
                    if is_exe(candidate):
                        return candidate

        raise ExecutableNotInstalledException(program)
        
    def call(self, commandline_arguments, *args, **kwargs):
        return subprocess.call([self.executable_file]+commandline_arguments, *args, **kwargs)
    def check_call(self, commandline_arguments, *args, **kwargs):
        return subprocess.check_call([self.executable_file]+commandline_arguments, *args, **kwargs)
    def Popen(self, commandline_arguments, *args, **kwargs):
        return subprocess.Popen([self.executable_file]+commandline_arguments, *args, **kwargs)


class Bzr(object):
    def __init__(self, directory):
        self.directory = directory

    def find_files(self):
        files = self.inventory()
        relative_path = self.get_relative_path()
        if relative_path is None:
            return []
        files_in_inventory = [self.adjusted(relative_path, filename) for filename in files if filename.startswith(relative_path)]
        return [f for f in files_in_inventory if os.path.exists(f)]

    def adjusted(self, relative_path, filename):
        if not relative_path:
            return filename
        return filename[len(relative_path):]
        
    def get_relative_path(self):
        bzr_root = self.find_bzr_root()
        cwd = os.getcwd()

        if not bzr_root:
            return None
        relative_path = ''
        if len(cwd) > len(bzr_root):
            relative_path = cwd[len(bzr_root)+1:]
        return os.path.join(relative_path, '')

    def find_bzr_root(self):
        bzr_root = os.path.join(os.getcwd(), self.directory)
        while bzr_root != '/' and not os.path.exists(os.path.join(bzr_root, '.bzr')):
            bzr_root = os.path.split(bzr_root)[0]
        if bzr_root != '/':
            return bzr_root
        return None
        
    def uses_bzr(self):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                try:
                    return_code = Executable('bzr').call(['info', self.directory], stdout=out, stderr=err)
                    return return_code == 0
                except Exception as ex:
                    logging.error('Error trying to execute "bzr info %s": %s' % (self.directory, ex))
                return False

    def inventory(self):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                bzr_args = 'inventory %s --kind=file' % self.directory
                try:
                    return_code = Executable('bzr').call(bzr_args.split(), stdout=out, stderr=err)
                    out.seek(0)
                    err.seek(0)
                    if not err.read():
                        files = out.read().split('\n')
                        return files
                except Exception as ex:
                    logging.error('Error trying to execute "bzr %s": %s' % (bzr_args, ex))
                return ['']

    def bzr_installed(self):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                try:
                    return_code = Executable('bzr').call([], stdout=out, stderr=err, shell=True)
                    return return_code == 0
                except OSError as ex:
                    if ex.errno == os.errno.ENOENT:
                        return False
                    else:
                        logging.error('Error trying to execute "bzr": %s' % ex)
                except ExecutableNotInstalledException as ex:
                    pass
                except Exception as ex:
                    logging.error('Error trying to execute "bzr": %s' % ex)
                return False
 
    def commit(self, message, unchanged=False):
        with file(os.devnull, 'w') as DEVNULL:
            args = '-m %s' % message
            if unchanged:
                args += ' --unchanged'
            return_code = Executable('bzr').call(('commit %s' % args).split(), cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)
        return return_code == 0
        
    def is_version_controlled(self):
        with file(os.devnull, 'w') as DEVNULL:
            return_code = Executable('bzr').call('info'.split(), cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)
        return return_code == 0

    def is_checked_in(self):
        with TemporaryFile() as out:
            return_code = Executable('bzr').call('status'.split(), cwd=self.directory, stdout=out, stderr=out)
            out.seek(0)
            return return_code == 0 and not out.read()

    @property
    def last_commit_time(self):
        with TemporaryFile() as out:
            with file(os.devnull, 'w') as DEVNULL:
                Executable('bzr').check_call('log -r -1'.split(), cwd=self.directory, stdout=out, stderr=DEVNULL)
                out.seek(0)
                [timestamp] = [line for line in out if line.startswith('timestamp')]
        timestamp = ' '.join(timestamp.split()[:-1]) # Cut off timezone
        return datetime.datetime.strptime(timestamp, 'timestamp: %a %Y-%m-%d %H:%M:%S')

    def tag(self, tag_string):
        with file(os.devnull, 'w') as DEVNULL:
            Executable('bzr').check_call(('tag %s' % tag_string).split(), cwd=self.directory, stdout=DEVNULL, stderr=DEVNULL)
        
    def get_tags(self, head_only=False):
        tags = []
        with TemporaryFile() as out:
            with file(os.devnull, 'w') as DEVNULL:
                head_only = ' -r -1 ' if head_only else ''
                Executable('bzr').check_call(('tags'+head_only).split(), cwd=self.directory, stdout=out, stderr=DEVNULL)
                out.seek(0)
                tags = [line.split()[0] for line in out if line]
        return tags 
 
 
 
        
def find_files(dirname):
    bzr = Bzr(dirname)
    if bzr.bzr_installed() and bzr.uses_bzr():
        return bzr.find_files()
    else:
        return []
