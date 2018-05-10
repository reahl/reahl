# Copyright 2016, 2017, 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import Fixture, scenario, expected, temp_dir, NoException
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EasterEgg, EmptyStub, stubclass, SystemOutStub

from reahl.doc.commands import Example, GetExample

"An example is code shipped in a python package that can be checked out by a user as separate example project."

"The imports absolute to the example's packaged location are made relative to render it a standalone copy of the packaged version."

"Certain files and directories are ignored when checking out the example."

"Some examples are whole packages, some are single modules."


class ExampleFixture(Fixture):
    example_name = 'theexample'
    example_module_contents = ''

    def new_containing_egg(self):
        egg = EasterEgg(name='example_egg', location=self.egg_directory.name)
        yield egg
        egg.deactivate()

    def new_egg_directory(self):
        return temp_dir()

    def new_examples_package_dir(self):
        directory = self.egg_directory.sub_dir('testexamples')
        directory.file_with('__init__.py', '')
        return directory

    def new_example_module(self):
        return self.examples_package_dir.file_with('theexample.py', self.example_module_contents)

    def new_checkout_directory(self):
        return temp_dir()

    def new_GetExample(self):
        @stubclass(GetExample)
        class GetExampleStub(GetExample):
            def create_example(self, name):
                return Example('testexamples', name)
        return GetExampleStub
    

class ImportErrorScenarios(ExampleFixture):
    @scenario
    def no_errors(self):
        self.example_module_contents = ''
        self.expected_exception = NoException
        self.command_line = [self.example_name]

    @scenario
    def nonexistant_example_error(self):
        self.example_module_contents = ''
        self.expected_exception = NoException
        self.command_line = ['anexamplethatdoesnotexist']

    @scenario
    def error_in_example_itself(self):
        self.example_module_contents = 'import somethingthatdoesnotexist'
        self.expected_exception = ImportError
        self.command_line = [self.example_name]


@with_fixtures(ImportErrorScenarios)
def test_handling_import_errors(import_error_scenarios):
    """Should example code be broken enough to cause ImportErrors, such errors are 
       reported when an attempt is made to check it out."""

    import_error_scenarios.example_module.change_contents(import_error_scenarios.example_module_contents)
    import_error_scenarios.containing_egg.activate()

    with SystemOutStub(), import_error_scenarios.checkout_directory.as_cwd():
        command = import_error_scenarios.GetExample()
        with expected(import_error_scenarios.expected_exception):
            command.do(import_error_scenarios.command_line)
