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



import os.path

from reahl.tofu import temp_file_with
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.modelinterface import FileField, ExposedNames, Event, UploadedFile, ValidationConstraint
from reahl.web.ui import SimpleFileInput, Form, ButtonInput
from reahl.browsertools.browsertools import XPath

from reahl.web_dev.fixtures import WebFixture


class FailingConstraint(ValidationConstraint):
    fail = True

    def validate_input(self, unparsed_input):
        if self.fail:
            raise self


@with_fixtures(WebFixture)
def test_form_encoding(web_fixture):
    """The enctype of a Form changes to multipart/form-data if it contains an input for a file."""
    fixture = web_fixture

    class DomainObject:
        fields = ExposedNames()
        fields.file = lambda i: FileField(allow_multiple=False, label='Attached files')

    domain_object = DomainObject()

    form = Form(fixture.view, 'testform')
    assert 'enctype' not in form.attributes.v

    form.add_child(SimpleFileInput(form, domain_object.fields.file))
    assert form.attributes.v['enctype'] == 'multipart/form-data'


@with_fixtures(WebFixture)
def test_simple_file_input(web_fixture):
    """A SimpleFileInput is a Widget with which a user can choose one or more files.
       The SimpleFileInput transforms the chosen files to UploadedFile objects, and passes these
       to its associated FileField upon a Form submit."""


    expected_content = b'some content'
    file_to_upload = temp_file_with(expected_content, mode='w+b')
    class DomainObject:
        def __init__(self):
           self.file = None

        fields = ExposedNames()
        fields.file = lambda i: FileField(allow_multiple=False, label='Attached files')

        events = ExposedNames()
        events.upload = lambda i: Event(label='Upload')

    domain_object = DomainObject()

    class FileUploadForm(Form):
        def __init__(self, view):
            super().__init__(view, 'test')
            self.add_child(SimpleFileInput(self, domain_object.fields.file))
            self.define_event_handler(domain_object.events.upload)
            self.add_child(ButtonInput(self, domain_object.events.upload))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=FileUploadForm.factory(), enable_js=False)
    web_fixture.reahl_server.set_app(wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    browser.type(XPath.input_of_type('file'), file_to_upload.name)
    browser.click(XPath.button_labelled('Upload'))
    assert isinstance(domain_object.file, UploadedFile)
    assert domain_object.file.filename == os.path.basename(file_to_upload.name)
    with domain_object.file.open() as opened_file:
        read_contents = opened_file.read()
    assert read_contents == expected_content


@with_fixtures(WebFixture)
def test_simple_file_input_exceptions(web_fixture):
    """Usually, when a DomainException happens during a form submit Inputs save the input they received so that
       such input can be pre-populated on the screen rendered by a subsequent GET for a user to correct
       possible mistakes and resubmit.

       In the case of a SimpleFileInput however, the UploadedFile objects that serve as user input
       to a SimpleFileInput are discarded when a DomainException happens.  This is because it is not
       possible to prepopulate its value using HTML or JS as this would be a security risk.
    """


    file_to_upload = temp_file_with('some content')
    failing_constraint = FailingConstraint('I am breaking')

    class DomainObject:
        def __init__(self):
            self.file = None

        fields = ExposedNames()
        def make_field(self):
            field = FileField(allow_multiple=False, label='Attached files')
            # FailingConstraint is declared in module level scope for it to be pickleable
            field.add_validation_constraint(failing_constraint)
            return field
        fields.file = make_field
        events = ExposedNames()
        events.upload = lambda i: Event(label='Upload')

    domain_object = DomainObject()

    class FileUploadForm(Form):
        def __init__(self, view):
            super().__init__(view, 'test')
            file_input = self.add_child(SimpleFileInput(self, domain_object.fields.file))
            if file_input.validation_error:
                self.add_child(self.create_error_label(file_input))
            self.define_event_handler(domain_object.events.upload)
            self.add_child(ButtonInput(self, domain_object.events.upload))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=FileUploadForm.factory(), enable_js=False)
    web_fixture.reahl_server.set_app(wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')
    
    browser.type(XPath.input_of_type('file'), file_to_upload.name)
    browser.click(XPath.button_labelled('Upload'))
    assert browser.is_element_present('//label[text()="I am breaking"]')

    # Message is cleared on second attempt
    failing_constraint.fail = False
    browser.type(XPath.input_of_type('file'), file_to_upload.name)
    browser.click(XPath.button_labelled('Upload'))
    assert not browser.is_element_present('//label[text()="I am breaking"]')
