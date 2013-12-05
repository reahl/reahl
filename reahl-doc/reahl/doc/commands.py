# Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import shutil
import pkg_resources
import codecs
import re

from reahl.dev.devshell import WorkspaceCommand


class Example(object):
    @classmethod
    def get_all(cls):
        parent = pkg_resources.resource_filename(u'reahl.doc', u'examples')
        examples = []
        for dirpath, dirnames, filenames in os.walk(parent): 
            current_package = dirpath[len(parent)+1:].replace(os.sep, u'.')
            if u'.reahlproject' in filenames:
                examples.append(Example(current_package))
                dirnames[:] = []
            else:
                for module in [os.path.splitext(f)[0] for f in filenames
                               if f.endswith(u'.py') and f != '__init__.py']:
                    if current_package:
                        module_path = u'%s.%s' % (current_package, module)
                    else:
                        module_path = module
                    examples.append(Example(module_path))
        return examples

    def __init__(self, name):
        self.name = name

    def is_package(self):
        name_as_path = self.name.replace(u'.', os.sep)
        return self.abs_path_to_package.endswith(name_as_path)

    @property
    def abs_path_to_package(self):
        return pkg_resources.resource_filename(u'.'.join([u'reahl.doc.examples', self.name]), u'')

    @property
    def module_name(self):
        return self.name.split(u'.')[-1]

    @property
    def absolute_path(self):
        if self.is_package():
            return self.abs_path_to_package
        else:
            module_filename = u'%s.py' % self.module_name
            return os.path.join(self.abs_path_to_package, module_filename)

    @property
    def relative_path(self):
        root_path = pkg_resources.resource_filename('reahl.doc.examples', '')
        return self.absolute_path[len(root_path):]

    @property
    def checkout_directory_name(self):
        return self.module_name

    @property
    def exists(self):
        try:
            return pkg_resources.resource_exists('reahl.doc.examples', self.relative_path.replace(os.sep, u'/'))
        except ImportError:
            return False

    @property
    def checkout_dest(self):
        return os.path.join(os.getcwd(), os.path.basename(self.absolute_path))

    @property
    def is_checked_out(self):
        return os.path.exists(self.checkout_dest)

    def check_out(self):
        if self.is_package():
            self.checkout_dir(self.absolute_path, self.checkout_dest)
        else:
            self.sed_file_to(self.absolute_path, self.checkout_dest)

    @property
    def is_i18n_example(self):
        return self.name == u'tutorial.i18nexample'

    def sed_file_to(self, source_filename, dest_filename):
        full_module_name = u'reahl.doc.examples.%s' % self.name
        print dest_filename
        with codecs.open(source_filename, 'r', 'utf-8') as source_file:
            with codecs.open(dest_filename, 'w', 'utf-8') as dest_file:
                for source_line in source_file:
                    if self.is_i18n_example:
                        source_line = source_line.replace(u'Translator(u\'reahl-doc\')', u'Translator(u\'i18nexample\')')
                    dest_file.write(source_line.replace(u'%s.' % full_module_name, u''))

    def checkout_dir(self, source, dest):
        files_to_rename = {u'reahl-doc.po': u'i18nexample.po',
                           u'reahl-doc':    u'i18nexample'}
        for dirpath, dirnames, filenames in os.walk(source):
            relative_dirpath = dirpath[len(source)+1:]
            dest_dirname = os.path.join(dest, relative_dirpath)
            os.mkdir(dest_dirname)
            for filename in [f for f in filenames if not re.match(u'.*(.pyc|~|.mo)$', f)]:
                source_filename = os.path.join(dirpath, filename)
                dest_filename = os.path.join(dest_dirname, filename)
                if self.is_i18n_example and filename in files_to_rename:
                    dest_filename = os.path.join(dest_dirname, files_to_rename[filename])
                if source_filename != os.path.join(source, u'__init__.py'):
                    self.sed_file_to(source_filename, dest_filename)
                        
    def delete(self):
        if os.path.isdir(self.checkout_dest):
            shutil.rmtree(self.checkout_dest)
        elif os.path.isfile(self.checkout_dest):
            os.remove(self.checkout_dest)
           

class ListExamples(WorkspaceCommand):
    """Lists available examples."""
    keyword = 'listexamples'
    def execute(self, options, args):
        for example in Example.get_all():
            print example.name


class GetExample(WorkspaceCommand):
    """Give you a copy of an example."""
    keyword = 'example'
    usage_args = '<example_name>'
    options = [('-f', '--force-overwrite', 
                dict(action='store_true', dest='force', default=False, help='overwrite an existing example if in the way'))]

    def verify_commandline(self, options, args):
        if len(args) != 1:
            self.parser.error('You need to specify one and only one example name as argument')
        if not Example(args[0]).exists:
            self.parser.error('Could not find example %s' % args[0])

    def execute(self, options, args):
        example = Example(args[0])

        if example.is_checked_out:
            if options.force:
                print 'Deleting %s, it is in the way' % os.path.abspath(example.checkout_dest)
                example.delete()
            else:
                print 'First remove %s, it is in the way' % os.path.abspath(example.checkout_dest)
                return 3
        print 'Checking out to %s' % os.path.abspath(example.checkout_dest)
        example.check_out()
