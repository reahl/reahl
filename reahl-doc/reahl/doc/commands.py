# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

import six

import os
import shutil
import pkg_resources
import codecs
import re

from reahl.dev.devshell import WorkspaceCommand


class CheckoutChanges(object):
    def __init__(self, example):
        self.example = example
        self.source_text_replacements = {}
        self.files_to_rename = {}
        
        full_module_name = 'reahl.doc.examples.%s' % self.example.name
        self.add_replace_text('%s.' % full_module_name, '')

    def add_replace_text(self, from_text, to_text):
        self.source_text_replacements[from_text] = to_text
        return to_text

    def add_file_rename(self, from_name, to_name):
        self.files_to_rename[from_name] = to_name
        return to_name

    def get_output_filename(self, source_file_path, dest_dirname):
        filename = os.path.basename(source_file_path)
        return os.path.join(dest_dirname, self.files_to_rename.get(filename, filename))

    def get_output_line(self, source_line):
        output_line = source_line
        for source_text, replacement_text in self.source_text_replacements.items():
            output_line = output_line.replace(source_text, replacement_text)
        return output_line


class Example(object):
    @classmethod
    def get_all(cls):
        parent = pkg_resources.resource_filename('reahl.doc', 'examples')
        examples = []
        for dirpath, dirnames, filenames in os.walk(parent): 
            current_package = dirpath[len(parent)+1:].replace(os.sep, '.')
            if '.reahlproject' in filenames:
                examples.append(Example('reahl.doc.examples', current_package))
                dirnames[:] = []
            else:
                for module in [os.path.splitext(f)[0] for f in filenames
                               if f.endswith('.py') and f != '__init__.py']:
                    if current_package:
                        module_path = '%s.%s' % (current_package, module)
                    else:
                        module_path = module
                    examples.append(Example('reahl.doc.examples', module_path))
        return examples

    def __init__(self, containing_package, name):
        self.name = name
        self.containing_package = containing_package

    def is_package(self):
        name_as_path = self.name.replace('.', os.sep)
        return self.abs_path_to_package.endswith(name_as_path)

    @property
    def abs_path_to_package(self):
        return pkg_resources.resource_filename('.'.join([self.containing_package, self.name]), '')

    @property
    def module_name(self):
        return self.name.split('.')[-1]

    @property
    def absolute_path(self):
        if self.is_package():
            return self.abs_path_to_package
        else:
            module_filename = '%s.py' % self.module_name
            return os.path.join(self.abs_path_to_package, module_filename)

    @property
    def relative_path(self):
        root_path = pkg_resources.resource_filename(self.containing_package, '')
        return self.absolute_path[len(root_path):]

    @property
    def checkout_directory_name(self):
        return self.module_name

    @property
    def exists(self):
        try:
            return pkg_resources.resource_exists(self.containing_package, self.relative_path.replace(os.sep, '/'))
        except ImportError as ex:
            if six.PY2 and str(ex).endswith(self.name):
                return False
            elif six.PY3 and ex.name == '.'.join([self.containing_package, self.name]):
                return False
            raise

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
    def checkout_changes(self):    
        if self.name == 'tutorial.i18nexamplebootstrap':
            changes = CheckoutChanges(self)
            changes.add_replace_text('Catalogue(\'reahl-doc\')', 'Catalogue(\'i18nexamplebootstrap\')')
            changes.add_file_rename('reahl-doc.po', 'i18nexamplebootstrap.po')
            changes.add_file_rename('reahl-doc', 'i18nexamplebootstrap')
            return changes        
        else:
            return CheckoutChanges(self)

    def checkout_dir(self, source, dest):
        for dirpath, dirnames, filenames in os.walk(source):
            relative_dirpath = dirpath[len(source)+1:]
            if re.match('.idea$', relative_dirpath):
                dirnames[:] = []
            else:
                dest_dirname = os.path.join(dest, relative_dirpath)
                os.mkdir(dest_dirname)
                for filename in [f for f in filenames if not re.match('.*(.pyc|~|.mo|.noseids)$', f)]:
                    source_file_path = os.path.join(dirpath, filename)
                    if source_file_path != os.path.join(source, '__init__.py'):
                        dest_file_path = self.checkout_changes.get_output_filename(source_file_path, dest_dirname)
                        self.sed_file_to(source_file_path, dest_file_path)

    def sed_file_to(self, source_file_path, dest_file_path):
        print(dest_file_path)
        with codecs.open(source_file_path, 'r', 'utf-8') as source_file:
            with codecs.open(dest_file_path, 'w', 'utf-8') as dest_file:
                for source_line in source_file:
                    dest_file.write(self.checkout_changes.get_output_line(source_line))

    def delete(self):
        if os.path.isdir(self.checkout_dest):
            shutil.rmtree(self.checkout_dest)
        elif os.path.isfile(self.checkout_dest):
            os.remove(self.checkout_dest)


class ListExamples(WorkspaceCommand):
    """Lists available examples."""
    keyword = 'listexamples'
    def execute(self, args):
        for example in Example.get_all():
            print(example.name)


class GetExample(WorkspaceCommand):
    """Give you a copy of an example."""
    keyword = 'example'

    def assemble(self):
        super(GetExample, self).assemble()
        self.parser.add_argument('-f', '--force-overwrite', action='store_true', dest='force', default=False,
                                 help='overwrite an existing example if in the way')
        self.parser.add_argument('example_name', help='the name of the wanted example')


    def verify_commandline(self, args):
        if not self.create_example(args.example_name).exists:
            self.parser.error('Could not find example %s' % args.example_name)

    def execute(self, args):
        example = self.create_example(args.example_name)

        if example.is_checked_out:
            if args.force:
                print('Deleting %s, it is in the way' % os.path.abspath(example.checkout_dest))
                example.delete()
            else:
                print('First remove %s, it is in the way' % os.path.abspath(example.checkout_dest))
                return 3
        print('Checking out to %s' % os.path.abspath(example.checkout_dest))
        example.check_out()

    def create_example(self, name):
        return Example('reahl.doc.examples', name)
        
        
        
        
        
        
