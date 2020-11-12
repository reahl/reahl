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

import tempfile
import os
import sys
import os.path
from contextlib import contextmanager

__all__ = ['temp_file_name', 'temp_file_with', 'temp_file_with', 'file_with', 
           'temp_dir', 'EmptyDirectory', 'AutomaticallyDeletedDirectory',
           'temp_dir', 'added_sys_path', 'preserved_sys_modules']


class AutomaticallyDeletedFile:
    def __init__(self, name, contents='', mode='w+'):
        self.name = name
        with open(name, mode) as f:
            f.write(contents)

    def __del__(self):
        if os.path.exists(self.name):
            os.remove(self.name)

    def change_contents(self, contents):
        with open(self.name, 'w') as f:
            f.write(contents)
        

def file_with(name, contents, mode='w+'):
    """Creates a file with the given `name` and `contents`. The file will be deleted
       automatically when it is garbage collected. The file is opened after creation, ready to be read.
       
       :param name: The full path name of the file to be created.
       :param contents: The contents of the file. Must text unless binary mode was specified, in which case bytes should be used.
       :keyword mode: The mode to open the file in, as per open() builtin.

    """
    return AutomaticallyDeletedFile(name, contents, mode)


class EmptyDirectory:
    def __init__(self, name):
        self.name = name
        if os.path.exists(self.name):
            self.rm()
        self.create()

    def create(self):
        os.mkdir(self.name)

    def rm(self):
        if os.path.exists(self.name):
            for root, dirs, files in os.walk(self.name, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.remove(filename)
                for name in dirs:
                    filename = os.path.join(root, name)
                    os.rmdir(filename)

            os.rmdir(self.name)


class AutomaticallyDeletedDirectory(EmptyDirectory):
    """A directory that is deleted upon being garbage collected.
    
       :param name: The full path name of the directory.
    """
    def __init__(self, name):
        super().__init__(name)
        self.entries = []

    def __del__(self):
        for f in self.entries:
            try:
                f.rm()
                del f
            except AttributeError:
                pass

        try:
            self.rm()
        except AttributeError:
            pass


    def file_with(self, name, contents, mode='w+'):
        """Returns a file inside this directory with the given `name` and `contents`.""" 
        if name is None:
            handle, full_name = tempfile.mkstemp(dir=self.name)
            name = os.path.basename(full_name)
        f = AutomaticallyDeletedFile('%s/%s' % (self.name, name), contents, mode)
        self.entries.append(f)
        return f

    def temp_dir(self):
        """Returns a directory inside this directory.""" 
        d = AutomaticallyDeletedTempDirectory(directory=self.name)
        self.entries.append(d)
        return d

    def sub_dir(self, name):
        """Returns a directory inside this directory with the given `name`.""" 
        d = AutomaticallyDeletedDirectory(os.path.join(self.name, name))
        self.entries.append(d)
        return d

    @contextmanager
    def as_cwd(self):
        pwd = os.getcwd()
        os.chdir(self.name)
        try:
            yield self.name
        finally:
            os.chdir(pwd)
        

class AutomaticallyDeletedTempDirectory(AutomaticallyDeletedDirectory):
    def __init__(self, directory=None):
        name = tempfile.mkdtemp(dir=directory)
        super().__init__(name)

def temp_dir():
    """Creates an :class:`AutomaticallyDeletedDirectory`."""
    return AutomaticallyDeletedTempDirectory()

def temp_file_name():
    """Returns a name that may be used for a temporary file that may be created and removed by a programmer."""
    temp_file = tempfile.NamedTemporaryFile()
    temp_file.close()
    return temp_file.name

def temp_file_with(contents, name=None, mode='w+'):
    """Returns an opened, named temp file with contents as supplied. If `name` is supplied, the file
       is created inside a temporary directory.

       :param contents: The contents of the file. Must text unless binary mode was specified, in which case bytes should be used.
       :keyword name: If given, the the name of the file (not including the file system path to it).
       :keyword mode: The mode to open the file in, as per open() builtin.

    """
    if name:
        directory = temp_dir()
        temp_file = directory.file_with(name, contents, mode=mode)
        temp_file.temp_dir = directory
    else:
        temp_file = tempfile.NamedTemporaryFile(mode=mode)
        temp_file.write(contents)
        temp_file.seek(0)
    return temp_file


@contextmanager
def added_sys_path(path):
    sys.path.append(path)
    try:
        yield
    finally:
        sys.path.remove(path)

@contextmanager
def preserved_sys_modules():
    saved_modules = list(sys.modules.keys())[:]
    try:
        yield
    finally:
        final_modules = list(sys.modules.keys())[:]
        added_modules = set(final_modules)-set(saved_modules)
        for i in added_modules:
            del sys.modules[i]

