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


import subprocess
import logging
import os
import os.path
from tempfile import TemporaryFile

# see http://packages.python.org/distribute/setuptools.html#adding-support-for-other-revision-control-systems

class Bzr(object):
    def find_files(self, dirname):
        files = self.inventory(dirname)
        relative_path = self.get_relative_path(dirname)
        if relative_path is None:
            return []
        files_in_inventory = [self.adjusted(relative_path, filename) for filename in files if filename.startswith(relative_path)]
        return [f for f in files_in_inventory if os.path.exists(f)]

    def adjusted(self, relative_path, filename):
        if not relative_path:
            return filename
        return filename[len(relative_path):]
        
    def get_relative_path(self, dirname):
        bzr_root = self.find_bzr_root(dirname)
        cwd = os.getcwd()

        if not bzr_root:
            return None
        relative_path = u''
        if len(cwd) > len(bzr_root):
            relative_path = cwd[len(bzr_root)+1:]
        return os.path.join(relative_path, u'')

    def find_bzr_root(self, dirname):
        bzr_root = os.path.join(os.getcwd(), dirname)
        while bzr_root != '/' and not os.path.exists(os.path.join(bzr_root, u'.bzr')):
            bzr_root = os.path.split(bzr_root)[0]
        if bzr_root != '/':
            return bzr_root
        return None
        
    def uses_bzr(self, dirname):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                cmd = 'bzr info %s' % dirname
                try:
                    return_code = subprocess.call(cmd.split(), stdout=out, stderr=err)
                    return return_code == 0
                except Exception, ex:
                    logging.error('Error trying to execute "%s": %s' % (cmd, ex))
                return False

    def inventory(self, dirname):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                cmd = 'bzr inventory %s --kind=file' % dirname
                try:
                    return_code = subprocess.call(cmd.split(), stdout=out, stderr=err)
                    out.seek(0)
                    err.seek(0)
                    if not err.read():
                        files = out.read().split('\n')
                        return files
                except Exception, ex:
                    logging.error('Error trying to execute "%s": %s' % (cmd, ex))
                return ['']

    def bzr_installed(self):
        with TemporaryFile() as err:
            with TemporaryFile() as out:
                try:
                    return_code = subprocess.call('bzr', stdout=out, stderr=err, shell=True)
                    return return_code == 0
                except OSError, ex:
                    if ex.errno == os.errno.ENOENT:
                        return False
                    else:
                        logging.error('Error trying to execute "%s": %s' % (cmd, ex))
                except Exception, ex:
                    logging.error('Error trying to execute "%s": %s' % (cmd, ex))
                return False
        
def find_files(dirname):
    bzr = Bzr()
    if bzr.bzr_installed() and bzr.uses_bzr(dirname):
        return bzr.find_files(dirname)
    else:
        return []
